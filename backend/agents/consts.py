"""LangGraph node name constants.

These constants define the names of nodes used in LangGraph workflows.
By centralizing node names here, you can update them in a single location
rather than changing them throughout the codebase when adding new nodes
or refactoring the graph structure.

When adding new nodes to the workflow, define their names here and reference
these constants when building the graph (e.g., in add_node() calls) and
when routing between nodes (e.g., in conditional edges).
"""

LLM_WITH_TOOL_NODE = "llm_with_tool_node"
LLM_WITH_MCP_TOOL_NODE = "llm_with_mcp_tool_node"
TOOL_NODE = "tool_node"
MCP_TOOL_NODE = "mcp_tool_node"
COMPRESS_SEARCH = "compress_search"
