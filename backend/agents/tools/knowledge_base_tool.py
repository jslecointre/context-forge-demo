import os
from typing import Any, Dict

from langchain_chroma.vectorstores import Chroma
from langchain_core.tools import tool

from langchain_ibm import WatsonxEmbeddings

from backend import PROJECT_ROOT

# from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames
embed_params = {
    # EmbedTextParamsMetaNames.TRUNCATE_INPUT_TOKENS: 3,
    # EmbedTextParamsMetaNames.RETURN_OPTIONS: {"input_text": True},
}
DB_DIR = f"{PROJECT_ROOT}/{os.getenv('VDB_DIR','store')}"
embeddings = WatsonxEmbeddings(
    model_id="intfloat/multilingual-e5-large",
    url=os.getenv("WATSONX_URL"),
    project_id=os.getenv("WATSONX_PROJECT_ID"),
    params=embed_params,
)


def _get_vector_store(collection_name: str = None) -> Chroma:
    """Create and return a Chroma vector store instance.

    Returns:
        Chroma: The vector store connected to the underwriting guidelines.
    """
    return Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name=collection_name,
    )


def _format_passage(doc, score: float, index: int) -> Dict[str, Any]:
    """Format a document into a passage dictionary.

    Args:
        doc: LangChain Document object.
        score: Relevance score from similarity search.
        index: Passage index number.

    Returns:
        Dictionary with passage information.
    """
    first_line = doc.page_content.split("\n")[0].strip() if doc.page_content else ""
    return {
        "passage_number": index,
        "title": first_line,
        "content": doc.page_content,
        "source": doc.metadata.get("source", ""),
        "relevance_score": round(score, 4),
    }


@tool(parse_docstring=True)
def check_underwriting_guidelines(query: str, insurer: str) -> Dict[str, Any]:
    """Search underwriting guidelines for life insurance information in str about a specific topic for a given insurer :  "BESAFE" or "MOONLIFE"

    This tool retrieves relevant passages from the underwriting guidelines for life insurance knowledge base
    to help answer query about insurance policies, risk assessment, medical conditions,
    lifestyle factors, and underwriting decisions. Use this tool when you need to find
    specific guidelines or policies related to underwriting query.

    Args:
        query: str Must be a string The query or topic to search for in the underwriting guidelines. Examples: "marijuana usage policy", "diabetes risk assessment", "What is the likely decision for smokers?"
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
    if insurer.lower() == "besafe":
        index_name = "langchain"
    elif insurer.lower() == "moonlife":
        index_name = "MOONLIFE"
    else:
        raise ValueError(f"Insurer {insurer} not recognized")

    vdb = _get_vector_store(collection_name=index_name)

    # Perform similarity search with relevance scores
    results = vdb.similarity_search_with_relevance_scores(query, k=5)

    # Format passages
    passages = [
        _format_passage(doc, score, i + 1) for i, (doc, score) in enumerate(results)
    ]

    # Create formatted context string for prompt usage
    formatted_lines = []
    for p in passages:
        formatted_lines.append(
            f"[Passage {p['passage_number']}]\n"
            f"Title: {p['title']}\n"
            f"Source: {p['source']}\n"
            f"Score: {p['relevance_score']}\n"
            f"Content:\n{p['content']}\n"
        )
    formatted_context = "\n---\n".join(formatted_lines)

    return {
        "query": query,
        "insurer": insurer,
        "num_results": len(passages),
        "passages": passages,
        "formatted_context": formatted_context,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=".env")

    # Test check_underwriting_guidelines tool
    question = "Asthma policy"
    print("\nTest: check_underwriting_guidelines")
    print(f"Query: {question}")
    print("=" * 60)

    result = check_underwriting_guidelines.invoke(
        {"query": question, "insurer": "BESAFE"}
    )

    print(f"Found {result['num_results']} relevant passages\n")
    print("Formatted context for prompt:")
    print("=" * 60)
    print(result["formatted_context"])
