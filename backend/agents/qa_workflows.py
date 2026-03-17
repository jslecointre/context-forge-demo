from langgraph.graph import END, START, StateGraph
from langgraph.types import Checkpointer

from backend import PROJECT_ROOT
from backend.agents.consts import (
    COMPRESS_SEARCH,
    LLM_WITH_TOOL_NODE,
    LLM_WITH_MCP_TOOL_NODE,
    TOOL_NODE,
    MCP_TOOL_NODE,
)
from backend.agents.nodes.qa_compress_search_node import compress_research
from backend.agents.nodes.qa_llm_call_node import llm_call, llm_call_mcp
from backend.agents.nodes.qa_should_continue import should_continue, should_continue_mcp
from backend.agents.nodes.qa_tool_node import tool_node, mcp_tool_node
from backend.agents.states.qa_states import QAState


class QAWorkflow:
    """
    QAWorkflow allows defining nodes and graphs for the FastAPI backend.

    This class provides a modular approach to building LangGraph workflows for question-answering
    tasks. It enables the creation of different workflow configurations by composing reusable
    nodes and defining their connections.

    The modular design allows new agents and workflows to be added to the backend with minimal
    code changes. New workflows can be created by:
    1. Adding new node definitions (if needed)
    2. Creating a new edge configuration method (e.g., `_add_new_workflow_edges`)
    3. Registering the workflow in the `workflows_dict` within `build_graph`

    This approach separates node definitions from workflow orchestration, making it easy to
    experiment with different agent architectures and add new capabilities.
    """

    def __init__(self):
        self.config_data = {}

    def _create_workflow(self) -> StateGraph:
        workflow = StateGraph(QAState)
        workflow.add_node(node=LLM_WITH_TOOL_NODE, action=llm_call)
        workflow.add_node(node=LLM_WITH_MCP_TOOL_NODE, action=llm_call_mcp)
        workflow.add_node(node=TOOL_NODE, action=tool_node)
        workflow.add_node(node=MCP_TOOL_NODE, action=mcp_tool_node)
        workflow.add_node(node=COMPRESS_SEARCH, action=compress_research)
        return workflow

    def _add_agent_assist_agentic_workflow_edges(self, workflow: StateGraph):
        workflow.add_edge(START, LLM_WITH_TOOL_NODE)
        workflow.add_conditional_edges(
            LLM_WITH_TOOL_NODE,
            should_continue,
            {TOOL_NODE: TOOL_NODE, COMPRESS_SEARCH: COMPRESS_SEARCH, END: END},
        )
        workflow.add_edge(TOOL_NODE, LLM_WITH_TOOL_NODE)
        workflow.add_edge(COMPRESS_SEARCH, END)

    def _add_agent_assist_mcp_agentic_workflow_edges(self, workflow: StateGraph):
        workflow.add_edge(START, LLM_WITH_MCP_TOOL_NODE)
        workflow.add_conditional_edges(
            LLM_WITH_MCP_TOOL_NODE,
            should_continue_mcp,
            {
                MCP_TOOL_NODE: MCP_TOOL_NODE,
                COMPRESS_SEARCH: COMPRESS_SEARCH,
                END: END,
            },
        )
        workflow.add_edge(MCP_TOOL_NODE, LLM_WITH_MCP_TOOL_NODE)
        workflow.add_edge(COMPRESS_SEARCH, END)

    def build_graph(
        self,
        checkpointer: Checkpointer,
        draw: bool = False,
        workflow_name: str = "simple_qa_workflow",
    ):
        workflow = self._create_workflow()

        # Define workflow dictionary with interrupt configuration
        workflows_dict = {
            "agent_assist_agentic_workflow": {
                "add_edges": self._add_agent_assist_agentic_workflow_edges,
                "interrupt_before": None,
            },
            "agent_assist_mcp_agentic_workflow": {
                "add_edges": self._add_agent_assist_mcp_agentic_workflow_edges,
                "interrupt_before": None,
            },
        }

        # Get the correct workflow configuration
        workflow_config = workflows_dict.get(workflow_name)
        if not workflow_config:
            raise ValueError(f"Workflow not found: {workflow_name}")

        workflow_config["add_edges"](workflow)

        # Compile with workflow-specific interrupt configuration
        compiled_graph = workflow.compile(
            checkpointer=checkpointer,
            interrupt_after=workflow_config.get("interrupt_after"),
        )

        if draw:
            compiled_graph.get_graph().draw_mermaid_png(
                output_file_path=f"{PROJECT_ROOT}/images/{workflow_name}.png"
            )
        return compiled_graph

    async def run(
        self, input_state: QAState, checkpointer: Checkpointer, config: dict = None
    ):
        compiled_graph = self.build_graph(checkpointer=checkpointer)
        return await compiled_graph.ainvoke(input=input_state, config=config or {})
