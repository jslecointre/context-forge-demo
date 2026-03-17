"""
State Definitions and Pydantic Schemas for Q&A Agent

This module defines the state objects and structured schemas used for
the Q&A agent workflow. The Q&A agent can answer queries either from its own
knowledge or by leveraging search tools such as Wikipedia to answer requests.
Wikipedia sources retrieved during the workflow are stored in the agent state.
"""

import operator

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, List, Optional, Sequence, TypedDict
from backend.schemas import RAGSource


class QAState(TypedDict):
    """
    State for the Q&A agent containing message history and query metadata.

    This state tracks the agent's conversation history, the user's query,
    Wikipedia sources retrieved during tool calls, and the final answer
    generated after workflow execution. The agent can answer queries from
    its own knowledge or by using search tools like Wikipedia, with all
    retrieved Wikipedia sources accumulated in the wikipedia_sources field.
    """

    query: str
    qa_messages: Annotated[Sequence[BaseMessage], add_messages]
    # sources collected
    collected_sources: Annotated[List[dict], operator.add]
    # answer received after workflow execution
    answer: str
    sources: Optional[List[RAGSource]] = None
    # set to True when a gateway or unrecoverable error occurred
    error: bool
