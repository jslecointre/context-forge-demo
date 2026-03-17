from langchain_core.tools import tool


@tool(parse_docstring=True)
async def research_complete() -> str:
    """
    Signals that research is complete and triggers the final answer generation.

    This tool is used to indicate that sufficient sources and information have been
    collected to provide a comprehensive answer to the end user's question. When
    called, it signals the workflow to stop gathering additional information and
    proceed to synthesize the collected research into a final response.

    Use this tool when:
    - You have gathered enough relevant information from multiple sources to answer
      the user's question comprehensively
    - The collected research covers the key aspects of the question
    - You have sufficient evidence and examples to provide a well-supported answer
    - Further research would not significantly improve the quality of the answer

    Returns:
        A confirmation message indicating that research is complete and the workflow
        will proceed to generate the final answer for the end user.

    """
    return "Research completed allowing to answer end-user query"
