from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig
from backend.agents.chains import qa_model
from backend.agents.consts import COMPRESS_SEARCH
from backend.agents.states.qa_states import QAState
from backend.logger import logger


def sanitize_messages_for_llm(messages: list, question: str) -> list:
    """Sanitize messages to ensure proper format for the LLM.

    Some LLM providers require:
    1. Every tool_call must have a matching ToolMessage response
    2. Last message must be from User or Tool role

    This function converts the conversation history to a clean format by:
    - Stripping tool_calls from AIMessages (keeping content only)
    - Converting ToolMessages to context in a HumanMessage

    Args:
        messages: List of conversation messages
        question: Original user question

    Returns:
        Sanitized list of messages safe for the LLM
    """
    sanitized = []
    tool_results = []

    for msg in messages:
        if isinstance(msg, HumanMessage):
            sanitized.append(msg)
        elif isinstance(msg, SystemMessage):
            sanitized.append(msg)
        elif isinstance(msg, AIMessage):
            # Strip tool_calls, keep only text content
            content = msg.content if msg.content else ""
            if content:
                sanitized.append(AIMessage(content=content))
        elif isinstance(msg, ToolMessage):
            # Collect tool results to include as context
            tool_name = getattr(msg, "name", "tool")
            tool_results.append(f"[{tool_name} result]: {msg.content}")

    # Add collected tool results as context if any
    if tool_results:
        tool_context = "\n\n".join(tool_results)
        sanitized.append(
            HumanMessage(
                content=f"Here is the information gathered from the tools:\n\n{tool_context}"
            )
        )

    # Ensure last message is from User
    if not sanitized or not isinstance(sanitized[-1], HumanMessage):
        sanitized.append(
            HumanMessage(
                content=(
                    f"Based on the information gathered above, please provide a comprehensive "
                    f"final answer to the original question: ```{question}```. if appropriate provide a list of citations used to produce the answer with a link of source in markdown format"
                )
            )
        )

    return sanitized


async def compress_research(state: QAState, config: RunnableConfig) -> dict:
    """LangGraph node used to summarize a final answer based on previous tool calls and sources gathered.

    This node generates the final answer by leveraging the information collected from
    previous tool calls and sources

    Args:
        state (QAState): The QA state containing query, messages, and gathered sources.

    Returns:
        dict: Updated QA workflow state with the final answer and updated messages.
    """
    logger.info(f"***{COMPRESS_SEARCH}***")
    question = state.get("query")

    try:
        raw_messages = list(state.get("qa_messages", []))

        messages = sanitize_messages_for_llm(raw_messages, question)

        logger.info(
            f"***{COMPRESS_SEARCH}*** Sending {len(messages)} sanitized messages to LLM"
        )

        response = await qa_model.with_config({"tags": ["qa_final_message"]}).ainvoke(
            input=messages
        )

        # Append final response to original messages for state update
        raw_messages.append(AIMessage(content=response.content))

    except Exception as e:
        logger.error(f"***{COMPRESS_SEARCH}*** Error: {e}")
        raise e

    return {"answer": response.content, "qa_messages": raw_messages}
