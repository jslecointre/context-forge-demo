#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info()    { printf "${BLUE}ℹ ${NC}%s\n" "$1"; }
print_success() { printf "${GREEN}✓${NC} %s\n" "$1"; }
print_error()   { printf "${RED}✗${NC} %s\n" "$1"; }
print_warning() { printf "${YELLOW}⚠${NC} %s\n" "$1"; }
print_header() {
    printf "\n${BLUE}═══════════════════════════════════════${NC}\n"
    printf "${BLUE}  %s${NC}\n" "$1"
    printf "${BLUE}═══════════════════════════════════════${NC}\n\n"
}

# Run a delete command but don't fail the script if the resource doesn't exist
safe_delete() {
    local description="$1"; shift
    print_info "Deleting: $description"
    if "$@"; then
        print_success "Deleted: $description"
    else
        print_warning "Could not delete (may not exist): $description"
    fi
}

# ---------------------------------------------------------------------------
# 1. Delete Agents
# ---------------------------------------------------------------------------
delete_agents() {
    print_header "Step 1 – Deleting Agents"
    safe_delete "insurance_broker_agent"  orchestrate agents remove -k native --name insurance_broker_agent
    safe_delete "insurance_analyst_agent" orchestrate agents remove -k native --name insurance_analyst_agent
}

# ---------------------------------------------------------------------------
# 2. Delete MCP Toolkits
# ---------------------------------------------------------------------------
delete_toolkits() {
    print_header "Step 2 – Deleting MCP Toolkits"
    safe_delete "broker_cf_v_mcp_server" orchestrate toolkits remove --name broker_cf_v_mcp_server
    safe_delete "analyst_cf_v_mcp_server" orchestrate toolkits remove --name analyst_cf_v_mcp_server
}

# ---------------------------------------------------------------------------
# 3. Delete Connections
# ---------------------------------------------------------------------------
delete_connections() {
    print_header "Step 3 – Deleting Connections"
    safe_delete "broker_context_forge" orchestrate connections remove --app-id broker_context_forge
    safe_delete "analyst_context_forge" orchestrate connections remove --app-id analyst_context_forge
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    print_header "ContextForge Insurance Demo – Delete Script"

    if ! command -v orchestrate &> /dev/null; then
        print_error "orchestrate CLI not found."
        exit 1
    fi

    # Load .env if present
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "${script_dir}/.env" ]; then
        print_info "Loading environment from ${script_dir}/.env"
        set -a; source "${script_dir}/.env"; set +a
    fi

    # Activate the WXO environment to refresh the token
    if [ -n "${WXO_ENV_NAME}" ]; then
        print_info "Activating environment: ${WXO_ENV_NAME}"
        orchestrate env activate "${WXO_ENV_NAME}"
    else
        print_warning "WXO_ENV_NAME not set — skipping env activate"
    fi

    local delete_type="${1:-all}"

    case "$delete_type" in
        agents)
            delete_agents
            ;;
        toolkits)
            delete_toolkits
            ;;
        connections)
            delete_connections
            ;;
        all)
            # Reverse order of creation: agents first, then toolkits, then connections
            delete_agents
            delete_toolkits
            delete_connections
            ;;
        *)
            print_error "Invalid argument: $delete_type"
            echo ""
            echo "Usage: $0 [agents|toolkits|connections|all]"
            echo ""
            echo "Options:"
            echo "  agents       - Delete agents only"
            echo "  toolkits     - Delete MCP toolkits only"
            echo "  connections  - Delete connections only"
            echo "  all          - Delete everything (default)"
            exit 1
            ;;
    esac

    print_header "Delete Complete"
    print_success "Done."
    echo ""
}

main "$@"
