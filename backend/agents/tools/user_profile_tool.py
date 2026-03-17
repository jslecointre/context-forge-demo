from typing import Any, Dict

from langchain_core.tools import tool


@tool(parse_docstring=True)
def get_customer_profile(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve customer profile information by client ID.

    This tool fetches customer profile data including personal information,
    address details, and insurance company affiliation. Use this tool when
    you need to look up customer information for policy inquiries or
    verification purposes.

    Args:
        first_name: customer's first name
        last_name: Customer's last name

    Returns:
        A dictionary containing customer profile information with the following keys:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - email: Customer's email address
            - phone: Customer's phone number
            - address: Dictionary with street, city, state, zip_code, country
            - insurance_company: Name of the insurance company
            - policy_number: Associated policy number
            - policy_type: Type of insurance policy
            - status: Account status (active/inactive)
    """
    # Mocked customer profile data
    if first_name == "John" and last_name == "Doe":
        insurance_company = "BESAFE"
    else:
        insurance_company = "MOONLIFE"
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": f"{last_name}.{last_name}@example.com",
        "phone": "+1-555-123-4567",
        "address": {
            "street": "123 Main Street",
            "city": "Toronto",
            "state": "Ontario",
            "zip_code": "M5V 1A1",
            "country": "Canada",
        },
        "insurer": insurance_company,
        "policy_number": "POL-POL-A1B2C3",
        "policy_type": "Life Insurance",
        "status": "active",
    }


@tool(parse_docstring=True)
def get_medical_condition(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve customer medical condition information.

    This tool fetches medical condition data for a customer including their
    health condition, severity level, and smoking status. Use this tool when
    you need to assess health-related information for insurance policy
    evaluations or claims processing.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary containing medical condition information with the following keys:
            - condition: The medical condition name (e.g., Asthma)
            - severity: Severity level of the condition (mild/moderate/severe)
            - smoking_status: Customer's smoking status (never/former/current)
    """
    # Mocked customer profile data
    if first_name == "John" and last_name == "Doe":
        condition = "Asthma"
        severity = "severe"
        smoking_status = "current"
    else:
        condition = "Epilepsy"
        severity = "Partial seizures - Age 33 - Poor degree of control"
        smoking_status = "non-smoker"

    return {
        "condition": condition,
        "severity": severity,
        "smoking_status": smoking_status,
    }


@tool(parse_docstring=True)
def update_address(first_name: str, last_name: str, new_address: str) -> Dict[str, Any]:
    """Update a customer's address in their profile.

    This tool updates the address associated with a customer's profile.
    Use this tool when a customer requests to change their registered
    address for correspondence or policy documentation purposes.

    Args:
        first_name: Customer's first name for identification.
        last_name: Customer's last name for identification.
        new_address: The new address to replace the existing one.

    Returns:
        A dictionary containing the update confirmation with the following keys:
            - address: The newly updated address.
    """
    # Mocked customer profile data
    return {"address": new_address, "first_name": first_name, "last_name": last_name}


if __name__ == "__main__":
    import json

    # Test get_customer_profile tool
    print("\nTest: get_customer_profile")
    print("=" * 50)
    result = get_customer_profile.invoke({"client_id": "CLT-001"})
    print(json.dumps(result, indent=2))
