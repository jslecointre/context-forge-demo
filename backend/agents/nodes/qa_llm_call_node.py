import os
import httpx
from langchain_core.callbacks.manager import dispatch_custom_event
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from pydantic import TypeAdapter
from backend.agents.chains import qa_model
from backend.agents.tools import get_mcp_tools, get_mcp_tools_context_forge
from backend.agents.consts import LLM_WITH_TOOL_NODE, LLM_WITH_MCP_TOOL_NODE
from backend.agents.prompts import (
    underwriting_knowledge_qa_prompt,
    underwriting_knowledge_qa_mcp_prompt,
    analyst_qa_mcp_prompt,
)
from backend.agents.states.qa_states import QAState
from backend.agents.tools.knowledge_base_tool import check_underwriting_guidelines
from backend.agents.tools.research_complete import research_complete  # noqa F401
from backend.agents.tools.user_profile_tool import (  # noqa F401
    get_customer_profile,
    get_medical_condition,
    update_address,
)
from backend.logger import logger


tools = [get_customer_profile, check_underwriting_guidelines, get_medical_condition]
tools_by_name = {tool.name: tool for tool in tools}


def generate_tool_descriptions(tools):
    """
    Generate a formatted string describing a list of StructuredTool objects.

    Args:
        tools (list): List of StructuredTool objects, each with `name` and `description` attributes.

    Returns:
        str: A numbered Markdown-style description of tools.
    """
    if not tools:
        return "No available tools."

    descriptions = []
    for i, tool in enumerate(tools, 1):
        short_desc = tool.description.split(".")[0]
        descriptions.append(f"{i}. **{tool.name}** : {short_desc.lower()}")

    return "\n".join(descriptions)


_GATEWAY_ERROR_TYPES = (
    httpx.HTTPStatusError,
    httpx.ConnectError,
    httpx.TimeoutException,
)


def _extract_gateway_error(e: BaseException) -> BaseException | None:
    """Recursively unwrap anyio/asyncio ExceptionGroup to find a gateway HTTP error."""
    if isinstance(e, _GATEWAY_ERROR_TYPES):
        return e
    if isinstance(e, BaseExceptionGroup):
        for sub in e.exceptions:
            found = _extract_gateway_error(sub)
            if found is not None:
                return found
    return None


def _dispatch_gateway_error(e: BaseException) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 403:
            msg = "Cannot connect to MCP gateway: access forbidden (403). Check your permissions."
        elif status == 401:
            msg = "Cannot connect to MCP gateway: unauthorized (401). Check your credentials."
        else:
            msg = f"Cannot connect to MCP gateway: HTTP {status} error."
    else:
        msg = f"Cannot connect to MCP gateway: {e}"
    logger.error(f"[MCP] Gateway error: {msg}")
    dispatch_custom_event("tool_call_request", f"❌ {msg}")
    payload = {"response": msg, "sources": [], "stop_reason": "error"}
    json_payload = TypeAdapter(dict).dump_json(payload).decode("utf-8")
    dispatch_custom_event("end_conversation", json_payload)
    return msg


async def llm_call_mcp(state: QAState, config: RunnableConfig):
    """LLM call node for the agent_assist_mcp_agentic_workflow that uses MCP tools.

    This node fetches tools dynamically from remote MCP servers
    (underwriting_guidelines, crm_tools, medical_tools) and binds them to the LLM.
    It analyzes the current conversation state and determines:
    1. Which MCP tool to call to gather information needed to answer the query
    2. What parameters to pass to the selected MCP tool

    Returns updated state with the model's response, which may include MCP tool calls.
    """
    query = state["query"]
    config_data = config["configurable"]
    context_forge = config_data["context_forge"]
    context_forge_token = config_data.get("context_forge_token")
    context_forge_virtual_mcp = config_data.get("context_forge_virtual_mcp")
    persona = config_data.get("persona")

    prompt = (
        underwriting_knowledge_qa_mcp_prompt
        if persona == "broker"
        else analyst_qa_mcp_prompt
    )

    is_first_call = not state.get("qa_messages")
    if is_first_call:
        messages = [HumanMessage(content=query)]
    else:
        messages = state.get("qa_messages")

    logger.info(
        f"***{LLM_WITH_MCP_TOOL_NODE} persona [{persona}] llm_call for agent assist : {query}***"
    )
    try:
        if context_forge:
            base_url = os.getenv(
                "CONTEXT_FORGE_BASE_URL", "http://mcp-context-forge-plugin:4444"
            )
            mcp_host = f"{base_url}/servers/{context_forge_virtual_mcp}"
            mcp_tools = await get_mcp_tools_context_forge(
                token=context_forge_token, mcp_host=mcp_host
            )
        else:
            mcp_tools = await get_mcp_tools()
    except Exception as e:
        gateway_err = _extract_gateway_error(e)
        if gateway_err is None:
            raise
        error_msg = _dispatch_gateway_error(gateway_err)
        return {"qa_messages": [AIMessage(content=error_msg)], "error": True}
    logger.info(f"***{LLM_WITH_MCP_TOOL_NODE} [{len(mcp_tools)}] AVAILABLE TOOLS***")
    model_with_tools = qa_model.bind_tools(mcp_tools)
    ai_response = await model_with_tools.ainvoke(
        [SystemMessage(content=prompt)] + messages,
        config={"tags": ["llm_call_mcp_node_message"]},
    )
    new_messages = (
        [HumanMessage(content=query), ai_response] if is_first_call else [ai_response]
    )
    return {"qa_messages": new_messages}


async def llm_call(state: QAState, config: RunnableConfig):
    """Node that decides which tool to call with which parameters to answer the user query.

    This node analyzes the current conversation state and determines:
    1. Which tool to call (e.g., get_customer_profile) to gather information needed to answer the query
    2. What parameters to pass to the selected tool (e.g., which Wikipedia page to retrieve)

    The model can call tools like Wikipedia to search for relevant information, or provide
    a final answer if sufficient information has been gathered.

    Returns updated state with the model's response, which may include tool calls.
    """
    query = state["query"]
    is_first_call = not state.get("qa_messages")
    if is_first_call:
        messages = [HumanMessage(content=query)]
    else:
        messages = state.get("qa_messages")

    logger.info(f"***{LLM_WITH_TOOL_NODE} llm_call for agent assist : {query}***")
    model_with_tools = qa_model.bind_tools(tools)
    tools_descriptions = generate_tool_descriptions(tools)
    ai_response = await model_with_tools.ainvoke(
        [
            SystemMessage(
                content=underwriting_knowledge_qa_prompt.format(
                    tools_descriptions=tools_descriptions
                )
            )
        ]
        + messages,
        config={"tags": ["llm_call_node_message"]},
    )
    new_messages = (
        [HumanMessage(content=query), ai_response] if is_first_call else [ai_response]
    )
    return {"qa_messages": new_messages}


if __name__ == "__main__":
    tools_descriptions = generate_tool_descriptions(tools)
    print(tools_descriptions)
