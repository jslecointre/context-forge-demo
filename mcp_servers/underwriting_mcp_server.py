from mcp.server.fastmcp import FastMCP
import os
from typing import Any, Dict
from pathlib import Path
from langchain_chroma.vectorstores import Chroma
from langchain_ibm import WatsonxEmbeddings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


DB_DIR = f"{PROJECT_ROOT}/{os.getenv('VDB_DIR','store')}"
embeddings = WatsonxEmbeddings(
    model_id="intfloat/multilingual-e5-large",
    url=os.getenv("WATSONX_URL"),
    project_id=os.getenv("WATSONX_PROJECT_ID"),
    params=None,
)

mcp = FastMCP(
    "UnderWriting MCP Server",
    port=int(os.getenv("MCP_PORT", "8007")),
    host=os.getenv("MCP_HOST", "0.0.0.0"),
)


def _get_vector_store(collection_name: str = None) -> Chroma:
    """Create and return a Chroma vector store instance."""
    return Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name=collection_name,
    )


def _format_passage(doc, score: float, index: int) -> Dict[str, Any]:
    """Format a document into a passage dictionary."""
    first_line = doc.page_content.split("\n")[0].strip() if doc.page_content else ""
    return {
        "passage_number": index,
        "title": first_line,
        "content": doc.page_content,
        "source": doc.metadata.get("source", ""),
        "relevance_score": round(score, 4),
    }


def _vector_search(query: str, insurer: str, k: int = 5) -> Dict[str, Any]:
    """Shared vector search logic used by multiple guideline tools."""
    if insurer.lower() == "besafe":
        index_name = "langchain"
    elif insurer.lower() == "moonlife":
        index_name = "MOONLIFE"
    else:
        raise ValueError(
            f"Insurer {insurer} not recognized. Use 'BESAFE' or 'MOONLIFE'."
        )

    vdb = _get_vector_store(collection_name=index_name)
    results = vdb.similarity_search_with_relevance_scores(query, k=k)
    passages = [
        _format_passage(doc, score, i + 1) for i, (doc, score) in enumerate(results)
    ]
    formatted_lines = []
    for p in passages:
        formatted_lines.append(
            f"[Passage {p['passage_number']}]\n"
            f"Title: {p['title']}\n"
            f"Source: {p['source']}\n"
            f"Score: {p['relevance_score']}\n"
            f"Content:\n{p['content']}\n"
        )
    return {
        "query": query,
        "insurer": insurer,
        "num_results": len(passages),
        "passages": passages,
        "formatted_context": "\n---\n".join(formatted_lines),
    }


# ---------------------------------------------------------------------------
# GUIDELINE SEARCH TOOLS
# (Vector-search tools with nearly identical behaviour but different names/params)
# ---------------------------------------------------------------------------


@mcp.tool()
def check_underwriting_guidelines(query: str, insurer: str) -> Dict[str, Any]:
    """Search underwriting guidelines with a natural query on one topic for life insurance information in str about a specific topic for a given insurer :  "BESAFE" or "MOONLIFE"

    This tool retrieves relevant passages from the underwriting guidelines for life insurance knowledge base
    to help answer query about insurance policies, risk assessment, medical conditions,
    lifestyle factors, and underwriting decisions. Use this tool when you need to find
    specific guidelines or policies related to underwriting query.

    Args:
        query: str Must be a natural language query on one specific topic to search for in the underwriting guidelines. Examples: "marijuana usage policy", "diabetes risk assessment", "What is the likely decision for smokers?"
        insurer: str The insurance company name to filter guidelines. "BESAFE" or "MOONLIFE"

    Returns:
        A dictionary containing:
            - query: The original search query
            - insurer: The insurance company filter applied
            - num_results: Number of relevant passages found
            - passages: List of relevant passages, each containing:
                - passage_number: Index of the passage
                - title: Title extracted from the passage
                - content: Full text content of the passage
                - source: Source URL or document reference
                - relevance_score: Similarity score (0-1, higher is more relevant)
            - formatted_context: Pre-formatted string of all passages for prompt usage
    """
    return _vector_search(query=query, insurer=insurer)


@mcp.tool()
def search_policy_rules(topic: str, insurer: str) -> Dict[str, Any]:
    """Search for insurance policy rules and conditions for a given topic and insurer.

    Queries the policy rules knowledge base to find applicable rules for a
    specific topic such as a medical condition, occupation, or lifestyle factor.
    Use when looking for rules that govern policy issuance rather than
    underwriting risk ratings.

    Args:
        topic: The policy rule topic to search for (e.g. "HIV", "hazardous occupation", "foreign travel").
        insurer: Insurance company whose rules apply  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary containing:
            - query: The topic searched
            - insurer: The insurer whose rules were searched
            - num_results: Number of matching rule passages
            - passages: List of relevant rule passages
            - formatted_context: Pre-formatted string for prompt usage
    """
    return _vector_search(query=topic, insurer=insurer)


@mcp.tool()
def search_exclusion_clauses(query: str, insurer: str) -> Dict[str, Any]:
    """Search for exclusion clauses in underwriting guidelines for a specific condition or risk.

    Retrieves passages describing what is excluded from coverage under a given
    insurer's policy. Use specifically when trying to identify exclusions rather
    than general guideline information.

    Args:
        query: The condition or risk factor to find exclusions for (e.g. "pre-existing cancer", "aviation").
        insurer: Insurance company to search  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - query: The exclusion topic searched
            - insurer: The insurer
            - num_results: Number of exclusion passages found
            - passages: List of exclusion passages
            - formatted_context: Pre-formatted string of exclusion passages
    """
    exclusion_query = f"exclusion clause {query}"
    return _vector_search(query=exclusion_query, insurer=insurer)


@mcp.tool()
def get_lifestyle_risk_guidelines(factor: str, insurer: str) -> Dict[str, Any]:
    """Retrieve underwriting guidelines specifically for lifestyle risk factors.

    Searches the guidelines for lifestyle-related underwriting rules such as
    smoking, alcohol, recreational drug use, or extreme sports. Use when the
    risk is lifestyle-driven rather than medical.

    Args:
        factor: The lifestyle factor to search guidelines for (e.g. "smoking", "alcohol", "skydiving", "marijuana").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - query: The lifestyle factor queried
            - insurer: The insurer whose guidelines were searched
            - num_results: Number of relevant passages found
            - passages: List of guideline passages
            - formatted_context: Pre-formatted string for prompt usage
    """
    lifestyle_query = f"lifestyle factor {factor} underwriting guidelines"
    return _vector_search(query=lifestyle_query, insurer=insurer)


@mcp.tool()
def query_coverage_guidelines(
    condition_or_topic: str, policy_type: str, insurer: str
) -> Dict[str, Any]:
    """Query coverage guidelines for a specific condition and policy type.

    Searches for coverage-related guidelines that explain what is covered
    or excluded for a particular combination of medical condition and insurance
    product type. Use when you need to determine coverage applicability rather
    than just risk rating.

    Args:
        condition_or_topic: Medical condition or topic (e.g. "Type 2 Diabetes", "epilepsy").
        policy_type: Type of insurance product (e.g. "Term Life", "Critical Illness", "Disability").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - query: The composed search query
            - insurer: The insurer
            - num_results: Number of matching passages
            - passages: List of coverage guideline passages
            - formatted_context: Pre-formatted string of results
    """
    composed_query = f"{condition_or_topic} coverage guidelines {policy_type}"
    return _vector_search(query=composed_query, insurer=insurer)


# ---------------------------------------------------------------------------
# RISK ASSESSMENT TOOLS
# (Mocked tools that return ratings  similar to each other and to health tools)
# ---------------------------------------------------------------------------


@mcp.tool()
def get_underwriting_decision(
    condition: str, severity: str, smoking_status: str, insurer: str
) -> Dict[str, Any]:
    """Get a preliminary underwriting decision for a given medical profile.

    Returns a suggested underwriting outcome based on a customer's primary
    condition, severity, and smoking status. This provides a decision recommendation,
    not just guideline text. Use after retrieving health data and guidelines.

    Args:
        condition: The primary medical condition (e.g. "Asthma", "Epilepsy").
        severity: The severity of the condition (e.g. "mild", "moderate", "severe").
        smoking_status: Customer's smoking status ("never", "former", "current").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - condition: The condition evaluated
            - severity: The severity provided
            - smoking_status: Smoking status provided
            - insurer: The insurer
            - decision: Underwriting decision (standard / rated / postpone / decline)
            - rating: Table rating if rated (e.g. "Table B", "Table D" or null)
            - flat_extra_per_1000: Any flat extra per $1,000 coverage
            - rationale: Brief explanation of the decision
    """
    return {}


@mcp.tool()
def assess_insurance_risk(
    medical_condition: str, lifestyle_factor: str, insurer: str
) -> Dict[str, Any]:
    """Assess insurance risk based on a combination of medical condition and lifestyle factor.

    Produces a risk assessment combining medical and lifestyle inputs. Use when
    you need an integrated risk view rather than a purely medical or lifestyle
    decision. Overlaps with get_underwriting_decision but takes different inputs.

    Args:
        medical_condition: The customer's primary medical condition.
        lifestyle_factor: A key lifestyle factor (e.g. "smoking", "obesity", "alcohol").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - medical_condition: Input condition
            - lifestyle_factor: Input lifestyle factor
            - insurer: The insurer
            - combined_risk_level: Overall risk level (low / medium / high / very_high)
            - recommended_action: Suggested underwriting action
            - premium_loading_percent: Suggested premium loading as a percentage
    """
    high_risk_conditions = {"asthma", "epilepsy", "diabetes", "heart disease", "cancer"}
    high_risk_lifestyle = {"smoking", "obesity", "alcohol abuse", "drug use"}

    condition_high = medical_condition.lower() in high_risk_conditions
    lifestyle_high = lifestyle_factor.lower() in high_risk_lifestyle

    if condition_high and lifestyle_high:
        return {
            "medical_condition": medical_condition,
            "lifestyle_factor": lifestyle_factor,
            "insurer": insurer,
            "combined_risk_level": "very_high",
            "recommended_action": "Substandard rating  refer to senior underwriter",
            "premium_loading_percent": 75,
        }
    if condition_high or lifestyle_high:
        return {
            "medical_condition": medical_condition,
            "lifestyle_factor": lifestyle_factor,
            "insurer": insurer,
            "combined_risk_level": "high",
            "recommended_action": "Rated  standard table rating applies",
            "premium_loading_percent": 40,
        }
    return {
        "medical_condition": medical_condition,
        "lifestyle_factor": lifestyle_factor,
        "insurer": insurer,
        "combined_risk_level": "low",
        "recommended_action": "Standard terms",
        "premium_loading_percent": 0,
    }


@mcp.tool()
def get_risk_rating(
    condition: str, severity: str, age: int, insurer: str
) -> Dict[str, Any]:
    """Get an actuarial risk rating for a condition, severity, and applicant age.

    Returns a risk rating that incorporates the age factor alongside medical
    severity. Use when age-adjusted risk is needed for pricing or product suitability.
    Differs from get_underwriting_decision in that it considers applicant age.

    Args:
        condition: The medical condition to rate.
        severity: Severity of the condition (mild / moderate / severe).
        age: Applicant's age in years.
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - condition: Input condition
            - severity: Input severity
            - age: Applicant age
            - insurer: The insurer
            - age_band: The age bracket applied (e.g. "18-30", "31-45", "46-60", "61+")
            - base_rating: Rating before age adjustment
            - age_adjusted_rating: Final rating after age factor
            - extra_premium_percent: Percentage loading above standard premium
    """
    if age < 31:
        age_band, age_factor = "18-30", 0.8
    elif age < 46:
        age_band, age_factor = "31-45", 1.0
    elif age < 61:
        age_band, age_factor = "46-60", 1.4
    else:
        age_band, age_factor = "61+", 2.0

    base_loading = {"mild": 25, "moderate": 50, "severe": 100}.get(severity.lower(), 50)
    adjusted_loading = int(base_loading * age_factor)

    return {
        "condition": condition,
        "severity": severity,
        "age": age,
        "insurer": insurer,
        "age_band": age_band,
        "base_rating": f"+{base_loading}%",
        "age_adjusted_rating": f"+{adjusted_loading}%",
        "extra_premium_percent": adjusted_loading,
    }


@mcp.tool()
def check_medical_exclusions(condition: str, insurer: str) -> Dict[str, Any]:
    """Check whether a medical condition triggers any standard policy exclusions.

    Returns exclusion information for a specific medical condition under a
    given insurer's standard policy wordings. Use when you need to know
    what exclusions would be applied rather than the overall risk rating.

    Args:
        condition: Medical condition to check for exclusions (e.g. "Asthma", "Epilepsy").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - condition: The condition checked
            - insurer: The insurer
            - exclusion_applies: Whether any exclusion is triggered (True/False)
            - exclusion_type: Type of exclusion ("full" / "partial" / "none")
            - excluded_benefits: List of benefit types excluded
            - exclusion_wording: Standard policy exclusion wording
    """
    return {}


@mcp.tool()
def get_premium_adjustment_factors(risk_category: str, insurer: str) -> Dict[str, Any]:
    """Retrieve the premium adjustment factor table for a given risk category and insurer.

    Returns the standard premium loading percentages and flat extras associated
    with each risk category. Use when you need to calculate the premium impact
    of a rating class rather than determine which rating applies.

    Args:
        risk_category: The underwriting risk category (e.g. "standard", "Table B", "Table D", "declined").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - risk_category: The queried risk category
            - insurer: The insurer
            - premium_loading_percent: Additional premium as a percentage of standard
            - flat_extra_per_1000: Additional flat premium per $1,000 sum insured
            - policy_restrictions: Any policy limits or restrictions at this rating
            - notes: Additional pricing notes
    """
    return {}


@mcp.tool()
def validate_insurance_application(
    first_name: str, last_name: str, insurer: str, product_type: str
) -> Dict[str, Any]:
    """Validate an insurance application by cross-checking CRM, health, and underwriting data.

    Performs a holistic application check that combines customer identity,
    health eligibility, and underwriting suitability. Use when you need a
    single-call validation before submitting an application, rather than
    calling individual tools separately.

    Note: This tool internally queries CRM and health data  do not call it
    alongside get_customer_profile or get_medical_condition for the same customer,
    as it will duplicate those lookups.

    Args:
        first_name: Applicant's first name.
        last_name: Applicant's last name.
        insurer: Target insurance company  "BESAFE" or "MOONLIFE".
        product_type: Insurance product being applied for (e.g. "Term Life", "Critical Illness").

    Returns:
        A dictionary with:
            - first_name: Applicant's first name
            - last_name: Applicant's last name
            - insurer: The insurer
            - product_type: The product
            - identity_verified: Whether CRM identity check passed
            - health_eligible: Whether the applicant passes health eligibility
            - underwriting_suitability: Preliminary suitability (suitable / rated / refer / decline)
            - application_status: Overall status (proceed / refer / decline)
            - notes: Any notes or flags from the validation
    """
    return {}


@mcp.tool()
def lookup_coverage_eligibility(
    condition: str, policy_type: str, insurer: str
) -> Dict[str, Any]:
    """Look up coverage eligibility for a specific medical condition and policy type.

    Checks whether a customer with a given condition can be covered under a
    specific policy type and what conditions or riders may be restricted. Use
    when assessing product suitability for a known medical condition.

    Args:
        condition: The medical condition to check eligibility for.
        policy_type: The insurance product type (e.g. "Term Life", "Whole Life", "Disability").
        insurer: Insurance company  "BESAFE" or "MOONLIFE".

    Returns:
        A dictionary with:
            - condition: The condition evaluated
            - policy_type: The product type
            - insurer: The insurer
            - coverage_available: Whether coverage can be offered (True/False)
            - available_riders: List of riders that can still be added
            - restricted_riders: List of riders that are excluded
            - max_coverage_amount: Maximum sum insured available (CAD, or null if declined)
    """
    return {}


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT1", "mcp").lower()
    if transport in ["mcp", "sse", "stdio"]:
        if transport == "mcp":
            transport = "streamable-http"

        mcp.run(transport=transport)
    else:
        raise Exception(f"Transport {transport} not supported")
