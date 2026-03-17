from mcp.server.fastmcp import FastMCP
from typing import Any, Dict, List
import os

mcp = FastMCP(
    "Health MCP Server",
    port=int(os.getenv("MCP_PORT", "8009")),
    host=os.getenv("MCP_HOST", "0.0.0.0"),
)


# ---------------------------------------------------------------------------
# MEDICAL CONDITION TOOLS
# ---------------------------------------------------------------------------


@mcp.tool()
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


@mcp.tool()
def fetch_health_record(first_name: str, last_name: str) -> Dict[str, Any]:
    """Fetch patient health record.

    This tool fetches medical condition data for a patient including their
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
    return {}


@mcp.tool()
def get_smoking_status(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve the smoking status for a customer.

    Returns only the smoking-related data for a customer. Use this specific
    tool when only smoking history is needed for premium calculation or
    underwriting classification.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - smoking_status: Current smoking status (never / former / current)
            - cigarettes_per_day: Average cigarettes per day (0 if non-smoker)
            - years_smoking: Number of years the customer has smoked
            - cessation_date: Date stopped smoking if former smoker (YYYY-MM-DD or null)
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "smoking_status": "current",
            "cigarettes_per_day": 15,
            "years_smoking": 12,
            "cessation_date": None,
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "smoking_status": "non-smoker",
        "cigarettes_per_day": 0,
        "years_smoking": 0,
        "cessation_date": None,
    }


@mcp.tool()
def get_lifestyle_factors(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve lifestyle and behavioural risk factors for a customer.

    Returns a broader lifestyle risk profile including smoking, alcohol
    consumption, physical activity, and BMI. Use when a full lifestyle
    picture is needed for risk scoring or underwriting, not just one factor.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - smoking_status: Smoking history (never / former / current)
            - alcohol_units_per_week: Average alcohol units per week
            - exercise_frequency: Exercise sessions per week
            - bmi: Body mass index
            - diet_quality: Self-reported diet quality (poor / fair / good / excellent)
            - occupation_risk: Occupational risk rating (low / medium / high)
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "smoking_status": "current",
            "alcohol_units_per_week": 18,
            "exercise_frequency": 1,
            "bmi": 27.4,
            "diet_quality": "poor",
            "occupation_risk": "low",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "smoking_status": "non-smoker",
        "alcohol_units_per_week": 4,
        "exercise_frequency": 4,
        "bmi": 23.1,
        "diet_quality": "good",
        "occupation_risk": "medium",
    }


@mcp.tool()
def assess_health_risk(first_name: str, last_name: str) -> Dict[str, Any]:
    """Assess the overall health risk profile for a customer.

    Produces an aggregated health risk score based on conditions, lifestyle,
    and medical history. Use when you need a single risk indicator for
    underwriting decisions rather than raw health data.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - risk_score: Numerical risk score (1–10, where 10 is highest risk)
            - risk_category: Categorical risk level (low / standard / substandard / declined)
            - primary_risk_factors: List of the main contributing risk factors
            - recommended_rating: Suggested underwriting rating class
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "risk_score": 8,
            "risk_category": "substandard",
            "primary_risk_factors": ["severe asthma", "current smoker", "elevated BMI"],
            "recommended_rating": "Table D",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "risk_score": 6,
        "risk_category": "substandard",
        "primary_risk_factors": ["epilepsy with poor control"],
        "recommended_rating": "Table C",
    }


@mcp.tool()
def get_chronic_conditions(first_name: str, last_name: str) -> List[Dict[str, Any]]:
    """Retrieve a list of chronic conditions diagnosed for a customer.

    Returns all chronic long-term conditions on record. Use when you need
    to enumerate all ongoing conditions rather than just the primary one.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A list of condition records, each containing:
            - condition_name: Name of the chronic condition
            - icd_code: ICD-10 diagnostic code
            - diagnosed_date: Date of first diagnosis (YYYY-MM-DD)
            - controlled: Whether the condition is currently controlled (True/False)
            - treating_physician: Name of the treating physician
    """
    return []


@mcp.tool()
def get_prescription_history(
    first_name: str, last_name: str, years: int = 3
) -> Dict[str, Any]:
    """Retrieve a customer's prescription medication history.

    Returns a log of medications prescribed over a specified number of years.
    Use when medication history is needed to understand treatment patterns
    or to flag high-risk medications for underwriting.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        years: Number of years of prescription history to retrieve (default 3).

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - years_covered: Number of years the history spans
            - prescriptions: List of prescription records, each with:
                - drug_name: Name of the medication
                - dosage: Prescribed dosage
                - start_date: When the prescription started (YYYY-MM-DD)
                - end_date: When it ended or null if ongoing
                - prescribing_physician: Name of the prescribing doctor
    """
    return {
        "first_name": first_name,
        "last_name": last_name,
        "years_covered": years,
        "prescriptions": [
            {
                "drug_name": "Salbutamol",
                "dosage": "100mcg inhaler",
                "start_date": "2022-01-10",
                "end_date": None,
                "prescribing_physician": "Dr. Sarah Lee",
            },
            {
                "drug_name": "Fluticasone",
                "dosage": "250mcg inhaler",
                "start_date": "2023-06-01",
                "end_date": None,
                "prescribing_physician": "Dr. Sarah Lee",
            },
        ],
    }


@mcp.tool()
def retrieve_medical_history(
    first_name: str, last_name: str, include_family_history: bool = False
) -> Dict[str, Any]:
    """Retrieve a customer's full medical history including past diagnoses and procedures.

    Returns a timeline of all recorded medical events, hospitalizations, and
    procedures. Optionally includes family medical history when relevant for
    hereditary risk assessment.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        include_family_history: Whether to include family history data (default False).

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - past_diagnoses: List of historical diagnoses
            - hospitalizations: Number of past hospitalizations
            - surgeries: List of past surgeries
            - family_history: Family history data (if requested), including hereditary conditions
    """
    result = {
        "first_name": first_name,
        "last_name": last_name,
        "past_diagnoses": [
            {"year": 2010, "condition": "Asthma", "resolved": False},
            {"year": 2018, "condition": "Pneumonia", "resolved": True},
        ],
        "hospitalizations": 1,
        "surgeries": [],
    }
    if include_family_history:
        result["family_history"] = {
            "father": ["Coronary artery disease", "Type 2 Diabetes"],
            "mother": ["Hypertension"],
            "siblings": ["Asthma"],
        }
    return result


@mcp.tool()
def check_health_eligibility(
    first_name: str, last_name: str, product_type: str
) -> Dict[str, Any]:
    """Check whether a customer is medically eligible for a specific insurance product.

    Evaluates the customer's health profile against the eligibility criteria for
    a given insurance product type. Returns an eligibility verdict and any
    exclusions that apply. Note: this does NOT apply underwriting guidelines
    use check_underwriting_guidelines for guideline lookups.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        product_type: Insurance product to check eligibility for (e.g. "Term Life", "Critical Illness").

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - product_type: The product evaluated
            - eligible: Whether the customer passes basic health eligibility
            - exclusions: List of conditions excluded from coverage
            - notes: Additional eligibility notes
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "product_type": product_type,
            "eligible": True,
            "exclusions": ["Respiratory-related claims excluded due to severe asthma"],
            "notes": "Smoker loading applies; standard rates not available.",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "product_type": product_type,
        "eligible": True,
        "exclusions": ["Neurological event exclusion for epilepsy"],
        "notes": "Substandard rating expected; refer to underwriting.",
    }


@mcp.tool()
def get_patient_bmi(first_name: str, last_name: str) -> Dict[str, Any]:
    """Retrieve the body mass index (BMI) measurement for a customer.

    Returns the most recent recorded BMI along with height and weight measurements.
    Use when body composition data is specifically required for build chart
    underwriting assessment.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - height_cm: Height in centimetres
            - weight_kg: Weight in kilograms
            - bmi: Calculated BMI value
            - bmi_category: WHO BMI category (underweight / normal / overweight / obese)
            - measurement_date: Date the measurement was recorded (YYYY-MM-DD)
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "height_cm": 178,
            "weight_kg": 87,
            "bmi": 27.4,
            "bmi_category": "overweight",
            "measurement_date": "2025-09-15",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "height_cm": 172,
        "weight_kg": 68,
        "bmi": 23.1,
        "bmi_category": "normal",
        "measurement_date": "2025-11-02",
    }


@mcp.tool()
def lookup_health_classification(first_name: str, last_name: str) -> Dict[str, Any]:
    """Look up the insurance health classification assigned to a customer.

    Returns the underwriting health class currently on file for the customer.
    Health classifications (Preferred, Standard, Substandard) affect premium rates.
    Use when you need the stored classification rather than computing it from raw data.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - health_class: Assigned insurance health class (Preferred / Standard / Substandard / Declined)
            - table_rating: Additional table rating if substandard (e.g. Table B, Table D)
            - flat_extra: Any flat extra premium per $1,000 of coverage
            - classification_date: Date the classification was last reviewed (YYYY-MM-DD)
            - reviewing_underwriter: ID of the underwriter who assigned the class
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "health_class": "Substandard",
            "table_rating": "Table D",
            "flat_extra": 3.50,
            "classification_date": "2025-01-10",
            "reviewing_underwriter": "UW-042",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "health_class": "Substandard",
        "table_rating": "Table C",
        "flat_extra": 0.0,
        "classification_date": "2025-02-28",
        "reviewing_underwriter": "UW-019",
    }


@mcp.tool()
def assess_mortality_risk(
    first_name: str, last_name: str, coverage_amount: int
) -> Dict[str, Any]:
    """Assess the mortality risk for a customer given a requested coverage amount.

    Combines health, lifestyle, and actuarial data to produce a mortality risk
    estimate. Use when computing expected mortality loading for large coverage
    amounts. This overlaps with underwriting but focuses on actuarial output.

    Args:
        first_name: Customer's first name.
        last_name: Customer's last name.
        coverage_amount: Requested coverage amount in CAD.

    Returns:
        A dictionary with:
            - first_name: Customer's first name
            - last_name: Customer's last name
            - coverage_amount: The requested coverage in CAD
            - mortality_ratio: Ratio to standard mortality (e.g. 175 means 175% of standard)
            - extra_mortality_per_1000: Additional premium per $1,000 sum insured
            - life_expectancy_adjustment_years: Estimated reduction in life expectancy
            - risk_verdict: Overall verdict (standard / rated / declined)
    """
    if first_name == "John" and last_name == "Doe":
        return {
            "first_name": first_name,
            "last_name": last_name,
            "coverage_amount": coverage_amount,
            "mortality_ratio": 200,
            "extra_mortality_per_1000": 5.00,
            "life_expectancy_adjustment_years": -8,
            "risk_verdict": "rated",
        }
    return {
        "first_name": first_name,
        "last_name": last_name,
        "coverage_amount": coverage_amount,
        "mortality_ratio": 175,
        "extra_mortality_per_1000": 3.50,
        "life_expectancy_adjustment_years": -5,
        "risk_verdict": "rated",
    }


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT1", "mcp").lower()
    if transport in ["mcp", "sse", "stdio"]:
        if transport == "mcp":
            transport = "streamable-http"

        mcp.run(transport=transport)
    else:
        raise Exception(f"Transport {transport} not supported")
