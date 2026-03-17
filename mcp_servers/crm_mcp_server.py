from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List
import os

mcp = FastMCP(
    "CRM MCP Server",
    port=int(os.getenv("MCP_PORT", "8008")),
    host=os.getenv("MCP_HOST", "0.0.0.0"),
)


@mcp.tool()
def get_client_id(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve the internal client ID for a customer by name.

    Looks up the CRM system and returns the unique client identifier
    associated with the given first and last name. Use this as a first step
    when you have a customer's name but need their ID for subsequent lookups.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - client_id: Unique client identifier (e.g. "POL-A1B2C3")
    """
    if first_name == "John" and last_name == "Doe":
        client_id = "POL-A1B2C3"
    else:
        client_id = "POL-D4E5F6"
    return {
        "first_name": first_name,
        "last_name": last_name,
        "client_id": client_id,
    }


@mcp.tool()
def get_customer_profile(client_id: str) -> Dict[str, Any]:
    """Retrieve customer profile information by client ID.

    Returns the customer profile data including personal information, address details, and insurance company affiliation. Use this tool when
    Use this when you know the policy number but not the customer's name.

    Args:
        client_id: Unique client identifier (e.g. "POL-A1B2C3").

    Returns:
        A dictionary containing customer profile information with the following keys:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - email: Customer's email address
            - phone: Customer's phone number
            - address: Dictionary with street, city, state, zip_code, country
            - insurer: Name of the insurance company
            - policy_number: Associated policy number
            - policy_type: Type of insurance policy
            - status: Account status (active/inactive)
    """
    return {}


@mcp.tool()
def lookup_policyholder(policy_number: str) -> Dict[str, Any]:
    """Look up a policyholder's CRM record using their policy number.

    Returns the customer details associated with a given insurance policy.
    Use this when you know the policy number but not the customer's name.

    Args:
        policy_number: The insurance policy reference number (e.g. "POL-POL-A1B2C3").

    Returns:
        A dictionary with:
            - policy_number: The queried policy number
            - first_name: Policyholder's first name
            - last_name: Policyholder's last name
            - date_of_birth: Date of birth (YYYY-MM-DD)
            - insurer: Insurance company associated with the policy
            - policy_type: Type of insurance product
            - policy_status: Current status of the policy
            - beneficiary: Named beneficiary on the policy
    """
    return {}


@mcp.tool()
def search_customer_by_name(full_name: str) -> List[Dict[str, Any]]:
    """Search for customers in the CRM system by their full name.

    Performs a fuzzy search across the customer database and returns matching
    records. Useful when you have the customer's name as a single string rather
    than split first/last. May return multiple matches.

    Args:
        full_name: Customer's full name as a single string (e.g. "John Doe").

    Returns:
        A list of matching customer summaries, each containing:
            - customer_id: Internal CRM identifier
            - full_name: Customer's full name
            - email: Email on file
            - insurer: Associated insurer
            - policy_number: Primary policy number
            - match_score: Fuzzy match confidence (0.0 – 1.0)
    """
    return []


@mcp.tool()
def get_contact_details(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve contact information for a customer.

    Returns only the contact-related fields (email, phone, address) for a
    given customer. Use this when you only need to reach the customer, not
    their full policy or health profile.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - email: Primary email address
            - phone: Primary phone number
            - address: Full mailing address (street, city, province, postal code)
            - preferred_contact_method: Customer's preferred contact channel
    """
    return {}


@mcp.tool()
def get_account_status(first_name: str, last_name: str) -> Dict[str, Any]:
    """Get the current account status and basic identifiers for a customer.

    Returns a lightweight summary focused on the account's standing  whether it is
    active, suspended, or lapsed. Use when you only need to verify account
    standing without loading the full profile.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - account_status: Current status (active / suspended / lapsed)
            - insurer: Affiliated insurer
            - policy_number: Primary policy reference
            - last_reviewed: Date the account was last reviewed (YYYY-MM-DD)
            - flags: List of any compliance or risk flags on the account
    """
    return {}


@mcp.tool()
def get_client_policy(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve policy-specific details for a customer from the CRM.

    Returns the insurance policy information associated with a customer.
    Use when you need policy details (number, type, coverage, premium) rather
    than personal or contact information.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - policy_number: Policy reference number
            - policy_type: Category of insurance (e.g. Life, Term, Whole)
            - insurer: Insurance company
            - coverage_amount: Sum insured in CAD
            - monthly_premium: Monthly premium amount in CAD
            - policy_start_date: Policy inception date (YYYY-MM-DD)
            - renewal_date: Next renewal date (YYYY-MM-DD)
            - beneficiary: Named beneficiary
    """
    return {}


@mcp.tool()
def retrieve_customer_history(
    first_name: str, last_name: str, limit: int = 10
) -> Dict[str, Any]:
    """Retrieve the interaction and change history for a customer's CRM record.

    Returns a log of past interactions, policy changes, address updates, and
    claims events. Use when auditing account activity or reviewing past
    service interactions.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        limit: Maximum number of history events to return (default 10).

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - total_events: Total number of recorded events
            - events: List of history events, each with:
                - date: Event date (YYYY-MM-DD)
                - type: Event category (address_change / claim / policy_update / contact)
                - description: Human-readable summary of the event
                - agent_id: ID of the agent who performed the action
    """
    return {
        "first_name": first_name,
        "last_name": last_name,
        "total_events": 3,
        "events": [
            {
                "date": "2025-08-10",
                "type": "address_change",
                "description": "Address updated from 45 Oak Ave to 123 Main Street.",
                "agent_id": "AGT-007",
            },
            {
                "date": "2025-03-22",
                "type": "contact",
                "description": "Customer called regarding premium payment.",
                "agent_id": "AGT-012",
            },
            {
                "date": "2024-01-15",
                "type": "policy_update",
                "description": "New Term Life Insurance policy POL-POL-A1B2C3 created.",
                "agent_id": "AGT-003",
            },
        ][:limit],
    }


@mcp.tool()
def find_clients_by_insurer(insurer_name: str) -> List[Dict[str, Any]]:
    """List all CRM customers affiliated with a specific insurance company.

    Returns a summary list of all clients whose primary insurer matches the
    given name. Use for reporting or batch processing workflows.

    Args:
        insurer_name: Name of the insurer (e.g. "BESAFE" or "MOONLIFE").

    Returns:
        A list of client summaries, each containing:
            - customer_id: Internal CRM identifier
            - full_name: Client's full name
            - policy_number: Primary policy number
            - policy_type: Type of insurance product
            - account_status: Current account status
    """
    if insurer_name.upper() == "BESAFE":
        clients = []
    else:
        clients = []
    return clients


# ---------------------------------------------------------------------------
# ADDRESS UPDATE TOOLS
# (Multiple ways to change address  ambiguous overlap)
# ---------------------------------------------------------------------------


@mcp.tool()
def update_address(client_id: str, new_address: str) -> Dict[str, Any]:
    """Update a customer's address in their profile.

    This tool updates the address associated with a customer's profile.

    Args:
        client_id: Customer's client_id
        new_address: The new address to replace the existing one.

    Returns:
        A dictionary containing the update confirmation with the following keys:
            - address: The newly updated address.
            - client_id:  Customer's client_id
    """
    return {"address": new_address, "client_id": client_id}


@mcp.tool()
def modify_contact_address(
    customer_id: str, new_address: str, address_type: str = "mailing"
) -> Dict[str, Any]:
    """Modify the mailing or billing address for a customer identified by ID.

    Updates the address in the CRM using the internal customer ID.
    Supports both mailing and billing address types. Use when you have
    a customer_id and do not require the old address for verification.

    Args:
        customer_id: Internal CRM identifier (e.g. "CLT-00123").
        new_address: The new address string to set.
        address_type: The type of address to update  "mailing" or "billing".

    Returns:
        A dictionary with:
            - customer_id: The identifier used
            - address_type: Which address type was updated
            - updated_address: The newly stored address
            - updated_at: Timestamp of the update (ISO 8601)
    """
    return {
        "customer_id": customer_id,
        "address_type": address_type,
        "updated_address": new_address,
        "updated_at": "2026-02-18T10:30:00Z",
    }


@mcp.tool()
def update_customer_record(
    first_name: str, last_name: str, field: str, value: str
) -> Dict[str, Any]:
    """Update a single field in a customer's CRM record.

    Generic field update tool that can modify any editable attribute of a
    customer record, including address, phone, email, or beneficiary.
    Use when you need to change one specific field rather than a full profile
    update.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        field: The name of the field to update (e.g. "address", "phone", "email", "beneficiary").
        value: The new value to set for that field.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - field_updated: The field that was changed
            - new_value: The value that was set
            - success: Boolean indicating whether the update succeeded
    """
    return {
        "first_name": first_name,
        "last_name": last_name,
        "field_updated": field,
        "new_value": value,
        "success": True,
    }


@mcp.tool()
def fetch_client_profile(client_id: str) -> Dict[str, Any]:
    """Retrieve profile

    Args:
        client_id: Unique client identifier (e.g. "POL-A1B2C3").

    Returns:
        A dictionary
    """
    if client_id == "POL-A1B2C3":
        insurance_company = "BESAFE"
        first_name = "John"
        last_name = "Doe"
    elif client_id == "POL-D4E5F6":
        insurance_company = "MOONLIFE"
        first_name = "Lea"
        last_name = "Kim"
    else:
        return {}
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{first_name.lower()}.{last_name.lower()}@example.com",
        "phone": "+1-555-123-4567",
        "address": {
            "street": "123 Main Street",
            "city": "Toronto",
            "state": "Ontario",
            "zip_code": "M5V 1A1",
            "country": "Canada",
        },
        "insurer": insurance_company,
        "policy_number": client_id,
        "policy_type": "Life Insurance",
        "status": "active",
    }


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT1", "mcp").lower()
    if transport in ["mcp", "sse", "stdio"]:
        if transport == "mcp":
            transport = "streamable-http"

        mcp.run(transport=transport)
    else:
        raise Exception(f"Transport {transport} not supported")
