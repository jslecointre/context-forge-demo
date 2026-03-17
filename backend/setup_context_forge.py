from __future__ import annotations
from urllib.parse import urlparse
import argparse
import json
import logging
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import NoReturn, Optional


def _build_logger(name: str) -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    log.addHandler(handler)
    return log


logger = _build_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Runtime defaults  (override via env vars or CLI arguments)
# ──────────────────────────────────────────────────────────────────────────────

DEFAULT_BASE_URL: str = os.getenv(
    "CONTEXT_FORGE_BASE_URL", "http://mcp-context-forge-plugin:4444"
)
DEFAULT_ADMIN_EMAIL: str = os.getenv("CONTEXT_FORGE_ADMIN_EMAIL", "admin@example.com")
DEFAULT_PASSWORD: str = os.getenv("CONTEXT_FORGE_DEFAULT_PASSWORD", "changeme")

_TRANSPORT_MAP = {"mcp": "STREAMABLEHTTP", "sse": "SSE"}


def _get_user_token(base_url: str, username: str, password: str) -> str:
    """Authenticate with username/password and return the access token."""
    parsed = urlparse(base_url)
    api_base = f"{parsed.scheme}://{parsed.netloc}"
    payload = json.dumps({"email": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{api_base}/auth/login",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode())
    return body["access_token"]


def _gateway_url(
    host_env: str, port_env: str, fallback_host: str, fallback_port: str
) -> str:
    host = os.getenv(host_env, fallback_host).rstrip("/")
    port = os.getenv(port_env, fallback_port)
    return f"{host}:{port}/mcp"


def _gateway_transport(env_key: str) -> str:
    val = os.getenv(env_key, "mcp").lower()
    return _TRANSPORT_MAP.get(val, val.upper())


# ──────────────────────────────────────────────────────────────────────────────
# Data models
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class UserSpec:
    """Specification for a platform user."""

    full_name: str
    email: str
    password: str = ""  # Empty → resolved to default_password at runtime
    is_active: bool = True


@dataclass
class TeamSpec:
    """Specification for a team and its initial members."""

    name: str
    description: str
    # Each entry: (email, role)  — role is "member" or "owner"
    members: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class GatewaySpec:
    """Specification for a public MCP gateway (upstream server)."""

    name: str
    url: str
    description: str
    transport: str
    visibility: str = "public"


@dataclass
class VirtualServerSpec:
    """Specification for a team-scoped virtual MCP server."""

    name: str
    description: str
    team_name: str  # Resolved to team_id at runtime
    desired_tools: list[tuple[str, str]]  # (gateway_name, tool_name)
    visibility: str = "team"
    owner_email: str = ""  # Empty → resolved to admin_email at runtime


# ──────────────────────────────────────────────────────────────────────────────
# Topology definition
# Edit this section to customise the demo environment.
# ──────────────────────────────────────────────────────────────────────────────

USERS: list[UserSpec] = [
    UserSpec(full_name="John Doe", email="john.broker@insurco.com"),
    UserSpec(full_name="Mary Doe", email="mary.analyst@insurco.com"),
]

TEAMS: list[TeamSpec] = [
    TeamSpec(
        name="Insurance Brokers",
        description="Brokers managing client policies, underwriting, and health assessments.",
        members=[("john.broker@insurco.com", "member")],
    ),
    TeamSpec(
        name="Insurance Analysts",
        description="Analysts accessing CRM data and managing client health records.",
        members=[("mary.analyst@insurco.com", "member")],
    ),
]

GATEWAYS: list[GatewaySpec] = [
    GatewaySpec(
        name="underwriting",
        url=_gateway_url("MCP_HOST1", "MCP_PORT1", "http://localhost", "8007"),
        description="Life insurance underwriting manuals — policy verification and rule checks.",
        transport=_gateway_transport("MCP_TRANSPORT1"),
        visibility="public",
    ),
    GatewaySpec(
        name="crm",
        url=_gateway_url("MCP_HOST2", "MCP_PORT2", "http://localhost", "8008"),
        description="Customer relationship management — profiles, IDs, and existing services.",
        transport=_gateway_transport("MCP_TRANSPORT2"),
        visibility="public",
    ),
    GatewaySpec(
        name="health",
        url=_gateway_url("MCP_HOST3", "MCP_PORT3", "http://localhost", "8009"),
        description="Customer medical reports and health condition data.",
        transport=_gateway_transport("MCP_TRANSPORT3"),
        visibility="public",
    ),
]

VIRTUAL_SERVERS: list[VirtualServerSpec] = [
    # ── Broker Gateway ────────────────────────────────────────────────────────
    # Full access: CRM lookups, underwriting checks, health condition retrieval.
    VirtualServerSpec(
        name="broker_gateway",
        description=(
            "Broker Gateway: complete insurance workflow — CRM client lookups, "
            "underwriting guideline verification, and health condition retrieval."
        ),
        team_name="Insurance Brokers",
        desired_tools=[
            ("crm", "crm-get-client-id"),
            ("crm", "crm-fetch-client-profile"),
            ("underwriting", "underwriting-check-underwriting-guidelines"),
            ("health", "health-get-medical-condition"),
        ],
        visibility="team",
    ),
    # ── Analysts Gateway ─────────────────────────────────────────────────────
    # Restricted access: CRM read-only + client address update via health gateway.
    VirtualServerSpec(
        name="analysts_gateway",
        description=(
            "Analysts Gateway: CRM data read access and client address updates "
            "for insurance analysts."
        ),
        team_name="Insurance Analysts",
        desired_tools=[
            ("crm", "crm-get-client-id"),
            ("crm", "crm-fetch-client-profile"),
            ("crm", "crm-update-address"),
            ("crm", "crm-modify-contact-address"),
        ],
        visibility="team",
    ),
]


# ──────────────────────────────────────────────────────────────────────────────
# JWT helpers
# ──────────────────────────────────────────────────────────────────────────────


def generate_admin_token(
    secret_key: str,
    username: str = DEFAULT_ADMIN_EMAIL,
    exp_minutes: int = 10_080,  # 7 days
) -> str:
    """Generate an HS256 admin JWT with all required claims."""
    try:
        import jwt  # PyJWT  # noqa: PLC0415
    except ImportError:
        _die("PyJWT not installed. Run: pip install PyJWT")

    now = datetime.now(timezone.utc)
    payload: dict = {
        "sub": username,
        "username": username,
        "iat": int(now.timestamp()),
        "iss": "mcp-gateway",
        "aud": "mcp-gateway",
        "jti": str(uuid.uuid4()),
        "is_admin": True,
        "user": {
            "email": username,
            "full_name": "Setup Script Admin",
            "is_admin": True,
            "auth_provider": "setup_script",
        },
        # teams: null + is_admin: true → admin bypass (normalize_token_teams returns None).
        # Missing teams key would resolve to [] (public-only) and be denied by
        # AdminAuthMiddleware's public-token guard before the user DB check.
        "teams": None,
    }
    if exp_minutes > 0:
        payload["exp"] = int((now + timedelta(minutes=exp_minutes)).timestamp())

    return jwt.encode(payload, secret_key, algorithm="HS256")


def resolve_admin_token(token: Optional[str], secret_key: Optional[str]) -> str:
    """Return a valid admin token, auto-generating one from *secret_key* if available."""
    if secret_key:
        tok = generate_admin_token(secret_key)
        _log_ok("Admin token generated from JWT secret")
        return tok
    if token:
        return token
    else:
        username = os.getenv("CONTEXT_FORGE_ADMIN_USERNAME", "admin@example.com")
        password = os.getenv("CONTEXT_FORGE_ADMIN_PASSWORD", "changeme")
        mcp_host = os.getenv(
            "CONTEXT_FORGE_BASE_URL", "http://mcp-context-forge-plugin:4444"
        )
        token = _get_user_token(mcp_host, username, password)
        return token
    _die(
        "No authentication supplied. Provide one of:\n"
        "  1. CONTEXT_FORGE_TOKEN env var\n"
        "  2. JWT_SECRET_KEY env var  (auto-generates admin token)\n"
        "  3. --token <jwt>  CLI argument\n"
        "  4. --jwt-secret <key>  CLI argument"
    )


# ──────────────────────────────────────────────────────────────────────────────
# HTTP client
# ──────────────────────────────────────────────────────────────────────────────


def api_request(
    method: str,
    url: str,
    token: str,
    payload: Optional[dict] = None,
) -> dict:
    """
    Execute a JSON REST call against the ContextForge API.

    Returns the parsed JSON response on success, or a dict with an "error"
    key on HTTP errors (never raises).
    """
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        logger.warning("    [HTTP %s %s] %s", exc.code, exc.reason, body[:400])
        try:
            return json.loads(body)
        except Exception:
            return {"error": body}
    except urllib.error.URLError as exc:
        # Network-level failure: DNS error, connection refused, timeout, etc.
        logger.error(
            "    [URLError] %s — is ContextForge reachable at %s?", exc.reason, url
        )
        return {"error": str(exc.reason)}


# ──────────────────────────────────────────────────────────────────────────────
# Console helpers
# ──────────────────────────────────────────────────────────────────────────────


def _log_ok(msg: str) -> None:
    logger.info("    \u2713 %s", msg)


def _log_warn(msg: str) -> None:
    logger.warning("    \u007e %s", msg)


def _log_fail(msg: str) -> None:
    logger.error("    \u2717 %s", msg)


def _die(msg: str) -> NoReturn:
    logger.critical("\n\u2717 FATAL: %s", msg)
    sys.exit(1)


def _section(title: str) -> None:
    bar = "\u2500" * 62
    logger.info("\n%s", bar)
    logger.info("  %s", title)
    logger.info(bar)


# ──────────────────────────────────────────────────────────────────────────────
# Generic API helpers
# ──────────────────────────────────────────────────────────────────────────────


def _list_resources(base_url: str, token: str, endpoint: str) -> list[dict]:
    """Fetch a collection; handles both list and paginated dict responses."""
    resp = api_request("GET", f"{base_url}/{endpoint}", token)
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        return resp.get("items", resp.get(endpoint.split("/")[-1], []))
    return []


def _find_by_name(resources: list[dict], name: str) -> Optional[dict]:
    return next((r for r in resources if r.get("name") == name), None)


def _is_conflict(resp: dict) -> bool:
    text = str(resp).lower()
    return "already exists" in text or "conflict" in text or "duplicate" in text


def _is_member_exists(resp: dict) -> bool:
    text = str(resp).lower()
    return "already" in text or ("member" in text and "id" not in resp)


# ──────────────────────────────────────────────────────────────────────────────
# Provisioning steps
# ──────────────────────────────────────────────────────────────────────────────


def provision_users(
    base_url: str,
    token: str,
    users: list[UserSpec],
    default_password: str,
) -> dict[str, str]:
    """
    Create platform users via the admin API.

    Returns:
        Mapping of email → user_id (id may be empty if resolution failed).
    """
    _section(f"Step 1/4 — Provisioning Users ({len(users)})")
    result: dict[str, str] = {}

    for i, user in enumerate(users, 1):
        password = user.password or default_password
        logger.info("\n  [%d/%d] %s  <%s>", i, len(users), user.full_name, user.email)

        resp = api_request(
            "POST",
            f"{base_url}/admin/users",
            token,
            {
                "email": user.email,
                "password": password,
                "full_name": user.full_name,
                "is_active": user.is_active,
            },
        )
        logger.info(f"RESP {resp}")
        uid: str = resp.get("id") or resp.get("user_id") or ""
        if uid or resp.get("email"):
            _log_ok(f"Created  id={uid or '(unknown)'}")
            result[user.email] = uid
            continue

        if _is_conflict(resp):
            _log_warn("Already exists — resolving existing user")
            all_users = _list_resources(base_url, token, "admin/users")
            match = next((u for u in all_users if u.get("email") == user.email), None)
            if match:
                uid = match.get("id", "")
                result[user.email] = uid
                _log_ok(f"Resolved  id={uid}")
            else:
                _log_fail(f"Cannot resolve existing user '{user.email}'")
        else:
            _log_fail(f"Failed to create user: {resp}")

    return result


def provision_teams(
    base_url: str,
    token: str,
    teams: list[TeamSpec],
) -> dict[str, str]:
    """
    Create teams and add their initial members.

    Returns:
        Mapping of team_name → team_id.
    """
    _section(f"Step 2/4 — Provisioning Teams ({len(teams)})")
    result: dict[str, str] = {}

    for i, team in enumerate(teams, 1):
        logger.info("\n  [%d/%d] %s", i, len(teams), team.name)

        resp = api_request(
            "POST",
            f"{base_url}/teams/",
            token,
            {"name": team.name, "description": team.description},
        )
        team_id: str = resp.get("id", "")

        if team_id:
            _log_ok(f"Created  id={team_id}")
        elif _is_conflict(resp):
            _log_warn("Already exists — resolving existing team")
            existing = _list_resources(base_url, token, "teams")
            match = _find_by_name(existing, team.name)
            if match:
                team_id = match["id"]
                _log_ok(f"Resolved  id={team_id}")
            else:
                _log_fail(f"Cannot resolve team '{team.name}'")
                continue
        else:
            _log_fail(f"Failed to create team: {resp}")
            continue

        result[team.name] = team_id

        # Add members
        # for email, role in team.members:
        #     member_resp = api_request(
        #         "POST",
        #         f"{base_url}/teams/{team_id}/members",
        #         token,
        #         {"email": email, "role": role},
        #     )
        #     if member_resp.get("id") or member_resp.get("email") or member_resp.get("user_email"):
        #         _log_ok(f"Member added: {email} ({role})")
        #     elif _is_member_exists(member_resp):
        #         _log_warn(f"Already a member: {email}")
        #     else:
        #         _log_fail(f"Could not add {email}: {member_resp}")

    return result


def provision_gateways(
    base_url: str,
    token: str,
    gateways: list[GatewaySpec],
    owner_email: str,
) -> dict[str, str]:
    """
    Register public MCP gateways.

    Returns:
        Mapping of gateway_name → gateway_id.
    """
    _section(f"Step 3/4 — Registering Public MCP Gateways ({len(gateways)})")
    result: dict[str, str] = {}

    for i, gw in enumerate(gateways, 1):
        logger.info("\n  [%d/%d] %s  \u2192  %s", i, len(gateways), gw.name, gw.url)

        resp = api_request(
            "POST",
            f"{base_url}/gateways",
            token,
            {
                "name": gw.name,
                "url": gw.url,
                "description": gw.description,
                "transport": gw.transport,
                "owner_email": owner_email,
                "visibility": gw.visibility,
            },
        )
        gw_id: str = resp.get("id", "")

        if gw_id:
            _log_ok(f"Registered  id={gw_id}")
            result[gw.name] = gw_id
        elif _is_conflict(resp):
            _log_warn("Already registered — resolving existing gateway")
            existing = _list_resources(base_url, token, "gateways")
            match = _find_by_name(existing, gw.name)
            if match:
                result[gw.name] = match["id"]
                _log_ok(f"Resolved  id={match['id']}")
            else:
                _log_fail(f"Cannot resolve gateway '{gw.name}'")
        else:
            _log_fail(f"Failed to register gateway '{gw.name}': {resp}")

    return result


def resolve_tool_ids(
    base_url: str,
    token: str,
    desired: list[tuple[str, str]],
    label: str = "",
    retries: int = 6,
    delay: float = 3.0,
) -> list[str]:
    """
    Wait for gateway tool discovery, then return the IDs for the desired tools.

    Each entry in *desired* is (gateway_name, tool_name).  Matching is done
    by tool name; gateway_name is used only for diagnostic messages.

    Args:
        retries: Maximum poll attempts before giving up.
        delay:   Seconds between poll attempts.

    Returns:
        List of resolved tool IDs (may be shorter than *desired* on timeout).
    """
    tag = f"[{label}] " if label else ""
    logger.info(
        "\n    %sResolving %d tool(s)  (gateway discovery in progress\u2026)",
        tag,
        len(desired),
    )

    for attempt in range(1, retries + 1):
        all_tools: list[dict] = _fetch_all_tools(base_url, token)
        found: list[str] = []
        missing: list[tuple[str, str]] = []

        for gw_name, tool_name in desired:
            match = next((t for t in all_tools if t.get("name") == tool_name), None)
            if match:
                found.append(match["id"])
                _log_ok(f"{gw_name}:{tool_name}  id={match['id']}")
            else:
                missing.append((gw_name, tool_name))

        if not missing:
            return found

        if attempt < retries:
            logger.info(
                "    %d tool(s) not yet visible (attempt %d/%d), retrying in %.0fs\u2026",
                len(missing),
                attempt,
                retries,
                delay,
            )
            time.sleep(delay)
        else:
            for gw_name, tool_name in missing:
                _log_fail(f"{gw_name}:{tool_name}  not found after {retries} attempts")

    # Best-effort: return whatever was discovered
    all_tools = _fetch_all_tools(base_url, token)
    return [
        t["id"]
        for _, tool_name in desired
        for t in all_tools
        if t.get("name") == tool_name
    ]


def _fetch_all_tools(base_url: str, token: str) -> list[dict]:
    resp = api_request("GET", f"{base_url}/tools", token)
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        return resp.get("items", resp.get("tools", []))
    return []


def provision_virtual_servers(
    base_url: str,
    token: str,
    servers: list[VirtualServerSpec],
    team_ids: dict[str, str],
    admin_email: str,
    tool_retries: int = 6,
    tool_retry_delay: float = 3.0,
) -> dict[str, str]:
    """Create team-scoped virtual MCP servers with resolved tool sets.

    Returns:
        Mapping of server_name → server_id for all successfully created/resolved servers.
    """
    _section(f"Step 4/4 — Creating Virtual Servers ({len(servers)})")
    result: dict[str, str] = {}

    for i, vs in enumerate(servers, 1):
        owner = vs.owner_email or admin_email
        logger.info(
            "\n  [%d/%d] %s  (team: %s)", i, len(servers), vs.name, vs.team_name
        )

        team_id = team_ids.get(vs.team_name)
        if not team_id:
            _log_fail(f"Team '{vs.team_name}' not found — skipping '{vs.name}'")
            continue

        tool_ids = resolve_tool_ids(
            base_url,
            token,
            vs.desired_tools,
            label=vs.name,
            retries=tool_retries,
            delay=tool_retry_delay,
        )

        if not tool_ids:
            _log_fail(f"No tools resolved for '{vs.name}' — skipping")
            continue

        resp = api_request(
            "POST",
            f"{base_url}/servers",
            token,
            {
                "server": {
                    "name": vs.name,
                    "description": vs.description,
                    "associated_tools": tool_ids,
                    "team_id": team_id,
                    "owner_email": owner,
                    "visibility": vs.visibility,
                }
            },
        )

        server_id: str = resp.get("id", "")
        if server_id:
            _log_ok(f"Created  id={server_id}")
            logger.info("    Team       : %s  (%s)", vs.team_name, team_id)
            logger.info("    Visibility : %s", vs.visibility)
            logger.info("    Tools      : %d", len(tool_ids))
            logger.info("    SSE url    : %s/servers/%s/sse", base_url, server_id)
            logger.info("    MCP url    : %s/servers/%s/mcp", base_url, server_id)
            result[vs.name] = server_id
        elif _is_conflict(resp):
            _log_warn(f"Virtual server '{vs.name}' already exists")
            existing = _list_resources(base_url, token, "servers")
            match = _find_by_name(existing, vs.name)
            if match:
                result[vs.name] = match["id"]
                _log_ok(f"Resolved  id={match['id']}")
        else:
            _log_fail(f"Failed to create '{vs.name}': {resp}")

    return result


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="setup_context_forge_insurance",
        description="Provision ContextForge for the Insurance demo environment.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-generate admin token from JWT secret
  export JWT_SECRET_KEY="your-secret-key"
  python setup_context_forge.py

  # Pass an existing admin token
  python setup_context_forge.py --token "eyJ0eXAi..."

  # Target a custom instance and override passwords
  python setup_context_forge.py \\
      --base-url http://localhost:4444 \\
      --jwt-secret my-secret \\
      --default-password "S3cur3P@ss!"

  # Skip user/team steps (idempotent re-runs)
  python setup_context_forge.py --skip-users --skip-teams
        """,
    )

    auth = p.add_argument_group("Authentication")
    auth.add_argument(
        "--token",
        metavar="JWT",
        default=os.getenv("CONTEXT_FORGE_TOKEN"),
        help="Admin Bearer token (env: CONTEXT_FORGE_TOKEN)",
    )
    auth.add_argument(
        "--jwt-secret",
        metavar="SECRET",
        default=os.getenv("JWT_SECRET_KEY"),
        help="JWT secret for auto-generating an admin token (env: JWT_SECRET_KEY)",
    )

    target = p.add_argument_group("Target")
    target.add_argument(
        "--base-url",
        metavar="URL",
        default=DEFAULT_BASE_URL,
        help=f"ContextForge base URL (env: CONTEXT_FORGE_BASE_URL, default: {DEFAULT_BASE_URL})",
    )
    target.add_argument(
        "--admin-email",
        metavar="EMAIL",
        default=DEFAULT_ADMIN_EMAIL,
        help="Admin email used as resource owner (env: CONTEXT_FORGE_ADMIN_EMAIL)",
    )
    target.add_argument(
        "--default-password",
        metavar="PASS",
        default=DEFAULT_PASSWORD,
        help="Default password for created users (env: CONTEXT_FORGE_DEFAULT_PASSWORD)",
    )

    flow = p.add_argument_group("Execution control")
    flow.add_argument(
        "--skip-users", action="store_true", help="Skip user provisioning"
    )
    flow.add_argument(
        "--skip-teams", action="store_true", help="Skip team provisioning"
    )
    flow.add_argument(
        "--skip-gateways", action="store_true", help="Skip gateway registration"
    )
    flow.add_argument(
        "--skip-servers", action="store_true", help="Skip virtual server creation"
    )

    tuning = p.add_argument_group("Tool discovery tuning")
    tuning.add_argument(
        "--tool-retries",
        type=int,
        default=6,
        metavar="N",
        help="Poll attempts when waiting for tool discovery (default: 6)",
    )
    tuning.add_argument(
        "--tool-retry-delay",
        type=float,
        default=3.0,
        metavar="SEC",
        help="Seconds between tool discovery polls (default: 3.0)",
    )

    return p


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    args = _build_parser().parse_args()
    base_url = args.base_url.rstrip("/")
    token = resolve_admin_token(args.token, args.jwt_secret)

    logger.info("\n%s", "=" * 62)
    logger.info("  ContextForge \u2014 Insurance Demo Setup")
    logger.info("%s", "=" * 62)
    logger.info("  Target   : %s", base_url)
    logger.info("  Admin    : %s", args.admin_email)
    logger.info("  Token    : %s\u2026", token[:40])

    # ── Connectivity + auth check ────────────────────────────────────────────
    # /health is public — use it to verify the host is reachable, then probe
    # an authenticated endpoint (/teams) to catch token issues early.
    health_resp = api_request("GET", f"{base_url}/health", token)
    if "error" in health_resp and not health_resp.get("status"):
        _die(
            f"Cannot reach ContextForge at {base_url}\n"
            f"  Reason : {health_resp['error']}\n"
            f"  Fix    : pass --base-url with the correct host, e.g.\n"
            f"           python setup_context_forge.py --base-url http://localhost:4444"
        )
    logger.info("  Health   : OK")

    auth_resp = api_request("GET", f"{base_url}/teams", token)
    if (
        auth_resp.get("detail")
        or "error" in auth_resp
        and not isinstance(auth_resp, list)
    ):
        detail = auth_resp.get("detail") or auth_resp.get("error", "unknown")
        _die(
            f"Token rejected by ContextForge (HTTP 403)\n"
            f"  Detail : {detail}\n"
            f"  Fix    : regenerate the token — ensure JWT_SECRET_KEY matches the\n"
            f"           server's secret, then re-run with --jwt-secret <key>"
        )
    logger.info("  Auth     : OK\n")

    team_ids: dict[str, str] = {}
    server_ids: dict[str, str] = {}

    # ── Step 1: Users ────────────────────────────────────────────────────────
    # if not args.skip_users:
    #     print(token)
    #     provision_users(base_url, token, USERS, args.default_password)
    # else:
    #     logger.info("\n  [skipped] User provisioning")

    # ── Step 2: Teams ────────────────────────────────────────────────────────
    if not args.skip_teams:
        team_ids = provision_teams(base_url, token, TEAMS)
    else:
        logger.info(
            "\n  [skipped] Team provisioning \u2014 resolving existing teams\u2026"
        )
        existing = _list_resources(base_url, token, "teams")
        for team in TEAMS:
            match = _find_by_name(existing, team.name)
            if match:
                team_ids[team.name] = match["id"]
                _log_ok(f"Resolved team '{team.name}' \u2192 id={match['id']}")
            else:
                _log_warn(
                    f"Team '{team.name}' not found \u2014 related virtual server will be skipped"
                )

    # ── Step 3: Gateways ─────────────────────────────────────────────────────
    if not args.skip_gateways:
        provision_gateways(base_url, token, GATEWAYS, args.admin_email)
    else:
        logger.info("\n  [skipped] Gateway registration")

    # ── Step 4: Virtual servers ───────────────────────────────────────────────
    if not args.skip_servers:
        if not team_ids:
            _die(
                "No team IDs available — cannot create virtual servers.\n"
                "  Either run without --skip-teams, or ensure teams already exist."
            )
        server_ids = provision_virtual_servers(
            base_url,
            token,
            VIRTUAL_SERVERS,
            team_ids,
            args.admin_email,
            tool_retries=args.tool_retries,
            tool_retry_delay=args.tool_retry_delay,
        )
    else:
        logger.info("\n  [skipped] Virtual server creation")

    # ── Summary ───────────────────────────────────────────────────────────────
    bar = "\u2500" * 62
    logger.info("\n%s", bar)
    logger.info("  \u2713 Setup complete")
    logger.info(bar)
    logger.info("")
    logger.info("  Users:")
    for u in USERS:
        logger.info("    \u2022 %s  <%s>", u.full_name, u.email)
    logger.info("")
    logger.info("  Teams:")
    for name, tid in team_ids.items():
        logger.info("    \u2022 %s  (id: %s)", name, tid)
    logger.info("")
    logger.info("  Virtual Servers:")
    for vs in VIRTUAL_SERVERS:
        tools_str = ", ".join(f"{g}:{t}" for g, t in vs.desired_tools)
        logger.info(
            "    \u2022 %s  [%s]  team=%s", vs.name, vs.visibility, vs.team_name
        )
        logger.info("        tools: %s", tools_str)
    logger.info("")

    # ── Post-setup environment variables ──────────────────────────────────────
    broker_vserver = server_ids.get("broker_gateway", "<not created>")
    analyst_vserver = server_ids.get("analysts_gateway", "<not created>")

    logger.info("\n%s", "=" * 62)
    logger.info("  Post-Setup Environment Variables")
    logger.info("  Copy these into your .env file.")
    logger.info("  Tokens must be created manually for each team in ContextForge.")
    logger.info("%s\n", "=" * 62)
    logger.info("BROKER_CONTEXT_FORGE_VSERVER=%s", broker_vserver)
    logger.info(
        "BROKER_CONTEXT_FORGE_TOKEN=<create a token for the Insurance Brokers team>"
    )
    logger.info("")
    logger.info("ANALYST_CONTEXT_FORGE_VSERVER=%s", analyst_vserver)
    logger.info(
        "ANALYST_CONTEXT_FORGE_TOKEN=<create a token for the Insurance Analysts team>"
    )
    logger.info("")


if __name__ == "__main__":
    main()
