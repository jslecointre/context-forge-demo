import json
import os
import time
import json_repair
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from backend.agents.tools import get_mcp_tools, get_mcp_tools_context_forge
from backend.agents.consts import TOOL_NODE, MCP_TOOL_NODE
from backend.agents.nodes.qa_llm_call_node import (
    tools_by_name,
    _dispatch_gateway_error,
    _extract_gateway_error,
)
from backend.agents.states.qa_states import QAState
from backend.logger import logger
from langchain_core.callbacks.manager import dispatch_custom_event


async def tool_node(state: QAState, config: RunnableConfig):
    """Execute all tool calls from the previous LLM response.
    Returns updated state with tool execution results.
    """
    logger.info(f"***{TOOL_NODE} NODE tool_node***")
    response = state["qa_messages"][-1]
    tool_calls = response.tool_calls

    if len(tool_calls) == 0:
        tool_calls_json = json_repair.repair_json(response.content, return_objects=True)
        fixed_tool_calls = tool_calls_json
        # fixed_tool_calls = fix_tool_calls(tool_call_list=tool_calls_json)
        # logger.info(f"Repaired tool calls : {fixed_tool_calls}")
        response = AIMessage(content="calling these tools", tool_calls=fixed_tool_calls)

    observations = []
    collected_sources = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]

        logger.info(f'Calling tool - [{tool}] - with args - [{tool_call["args"]}]')
        tool_call_result = await tool.ainvoke(tool_call["args"])

        if tool_call["name"].startswith("check_underwriting"):
            logger.info(f"{TOOL_NODE} knowledge_base tool call ")
            collected_sources.append(tool_call_result.get("formatted_context"))

        # if tool_call["name"] == "research_complete":
        #     logger.info(f'{TOOL_NODE} research_complete tool call ')
        #     complete_messages.append(AIMessage(content=f"research is complete to answer {state['query']}"))

        logger.info(f"tool call results - [{tool_call_result}]")
        observations.append(tool_call_result)

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation, name=tool_call["name"], tool_call_id=tool_call["id"]
        )
        for observation, tool_call in zip(observations, tool_calls)
    ]

    return {"qa_messages": tool_outputs, "collected_sources": collected_sources}


async def mcp_tool_node(state: QAState, config: RunnableConfig):
    """Execute MCP tool calls from the previous llm_call_mcp response in the agent_assist_mcp_agentic_workflow.

    Processes tool calls issued by the LLM against MCP servers
    (underwriting_guidelines, crm_tools, medical_tools) and returns updated state
    with tool execution results.
    """
    config_data = config["configurable"]
    context_forge = config_data["context_forge"]
    context_forge_token = config_data.get("context_forge_token")
    context_forge_virtual_mcp = config_data.get("context_forge_virtual_mcp")
    logger.info(
        f"***{MCP_TOOL_NODE} NODE tool_node with context_forge [{context_forge}]***"
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
        return {
            "qa_messages": [AIMessage(content=error_msg)],
            "collected_sources": [],
            "error": True,
        }
    mcp_tools_by_name = {tool.name: tool for tool in mcp_tools}
    logger.info(
        f"***{MCP_TOOL_NODE} [{len(mcp_tools)}] AVAILABLE TOOLS [{mcp_tools_by_name}]***"
    )
    response = state["qa_messages"][-1]
    tool_calls = response.tool_calls

    if len(tool_calls) == 0:
        tool_calls_json = json_repair.repair_json(response.content, return_objects=True)
        fixed_tool_calls = tool_calls_json
        # fixed_tool_calls = fix_tool_calls(tool_call_list=tool_calls_json)
        # logger.info(f"Repaired tool calls : {fixed_tool_calls}")
        response = AIMessage(content="calling these tools", tool_calls=fixed_tool_calls)

    observations = []
    collected_sources = []
    for tool_call in tool_calls:
        tool = mcp_tools_by_name[tool_call["name"]]

        logger.info(f'Calling tool - [{tool}] - with args - [{tool_call["args"]}]')
        t0 = time.perf_counter()
        try:
            tool_call_result = await tool.ainvoke(tool_call["args"])
        except Exception as e:
            gateway_err = _extract_gateway_error(e)
            if gateway_err is None:
                raise
            error_msg = _dispatch_gateway_error(gateway_err)
            return {
                "qa_messages": [AIMessage(content=error_msg)],
                "collected_sources": [],
                "error": True,
            }
        elapsed_ms = (time.perf_counter() - t0) * 1000
        result_text = (
            tool_call_result[0].get("text", "empty")
            if isinstance(tool_call_result, list) and tool_call_result
            else "empty"
        )

        dispatch_custom_event(
            "tool_call_request",
            f'🔧 tool call {tool_call["name"]} with parameters {tool_call["args"]} \n\n✅ result ({elapsed_ms:.0f}ms) : {result_text}',
        )
        if tool_call["name"].startswith("check_underwriting"):
            logger.info(f"{MCP_TOOL_NODE} knowledge_base tool call ")

            # MCP tools return serialized content (list or str), not the original dict
            if isinstance(tool_call_result, dict):
                collected_sources.append(tool_call_result.get("formatted_context"))
            else:
                # Extract text from MCP content blocks (list) or plain string
                text = (
                    tool_call_result[0].get("text")
                    if isinstance(tool_call_result, list)
                    else tool_call_result.get("text")
                )
                parsed = json.loads(str(text))
                collected_sources.append(parsed.get("formatted_context"))

        # if tool_call["name"] == "research_complete":
        #     logger.info(f'{TOOL_NODE} research_complete tool call ')
        #     complete_messages.append(AIMessage(content=f"research is complete to answer {state['query']}"))

        logger.info(f"tool call results - [{tool_call_result}]")
        observations.append(tool_call_result)

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation, name=tool_call["name"], tool_call_id=tool_call["id"]
        )
        for observation, tool_call in zip(observations, tool_calls)
    ]

    return {"qa_messages": tool_outputs, "collected_sources": collected_sources}
