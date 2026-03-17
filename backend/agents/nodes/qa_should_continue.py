from typing import Literal

from langchain_core.runnables import RunnableConfig

from backend.agents.consts import COMPRESS_SEARCH, TOOL_NODE, MCP_TOOL_NODE
from backend.agents.states.qa_states import QAState
from langgraph.graph import END


def should_continue(
    state: QAState, config: RunnableConfig
) -> Literal["tool_node", "compress_research"]:
    """Conditional edge function for LangGraph that decides which node to invoke next.

    This function serves as a conditional edge in the LangGraph workflow, routing
    the execution flow based on whether the LLM's last message contains tool calls.

    Logic:
        - If the LLM answer has tool calls: route to `tool_node` to execute the tools
        - If the list of tool calls is empty: route to `compress_search` to compress
          research and generate the final answer

    Note:
        This logic can be modified if the `research_complete` tool is used, since in
        that case the last message will have tool calls even when research is complete.

    Args:
        state: The current QAState containing the conversation messages

    Returns:
        "tool_node": Continue to tool execution node when tool calls are present
        "compress_search": Stop research and compress results into final answer when
            no tool calls are present
    """
    messages = state["qa_messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return TOOL_NODE
    return COMPRESS_SEARCH

    # messages = state["qa_messages"]
    # last_message = messages[-1]
    # if last_message.tool_calls and last_message.tool_calls[-1].get('name') != 'research_complete':
    #     return TOOL_NODE
    # return COMPRESS_SEARCH


def should_continue_mcp(
    state: QAState, config: RunnableConfig
) -> Literal["mcp_tool_node", "compress_research"]:
    """Conditional edge function for LangGraph that decides which node to invoke next.

    This function serves as a conditional edge in the LangGraph workflow, routing
    the execution flow based on whether the LLM's last message contains tool calls.

    Logic:
        - If the LLM answer has tool calls: route to `tool_node` to execute the tools
        - If the list of tool calls is empty: route to `compress_search` to compress
          research and generate the final answer

    Note:
        This logic can be modified if the `research_complete` tool is used, since in
        that case the last message will have tool calls even when research is complete.

    Args:
        state: The current QAState containing the conversation messages

    Returns:
        "mcp_tool_node": Continue to tool execution node when tool calls are present
        "compress_search": Stop research and compress results into final answer when
            no tool calls are present
    """
    if state["error"]:
        return END
    messages = state["qa_messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return MCP_TOOL_NODE
    return COMPRESS_SEARCH

    # messages = state["qa_messages"]
    # last_message = messages[-1]
    # if last_message.tool_calls and last_message.tool_calls[-1].get('name') != 'research_complete':
    #     return TOOL_NODE
    # return COMPRESS_SEARCH
