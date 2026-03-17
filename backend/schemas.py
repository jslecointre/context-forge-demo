from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, BeforeValidator, HttpUrl, TypeAdapter
from typing_extensions import Annotated


class Workflow(str, Enum):
    AGENT_ASSIST_AGENTIC_WORKFLOW = "agent_assist_agentic_workflow"
    AGENT_ASSIST_MCP_AGENTIC_WORKFLOW = "agent_assist_mcp_agentic_workflow"


class VirtualMCP(str, Enum):
    BROKER = "broker_gateway"
    ANALYST = "analysts_gateway"
    DIRECT = "direct"


http_url_adapter = TypeAdapter(HttpUrl)
Url = Annotated[
    str, BeforeValidator(lambda value: str(http_url_adapter.validate_python(value)))
]


class RAGSource(BaseModel):
    # url: HttpUrl  # page url
    # url: Url
    url: str
    text_llm: Optional[str]  # section text_llm
    text: Optional[str]  # section text
    title: str  # page title
    id: Optional[str]  # document id
    score: float  # final score= initial score or reranked score
    es_score: Optional[float] = None  # initial score by es query
    content_type: Optional[str] = None
    description: Optional[str] = None


class QARequestWithWorkflow(BaseModel):
    """Q&A request with selected LangGraph workflow.

    Question-Answer query that will be processed by a selected LangGraph workflow.
    The workflow determines the specific processing pipeline used to generate the response.
    """

    query: str
    workflow: Workflow = Workflow.AGENT_ASSIST_AGENTIC_WORKFLOW
    context_forge_virtual_mcp: Optional[VirtualMCP] = VirtualMCP.DIRECT
    context_forge_token: Optional[str] = None
    thread_id: Optional[str] = None
    k: Optional[int] = 3
    context_forge: Optional[bool] = False


class SimpleQAResponse(BaseModel):
    query: str
    response: str
    thread_id: str = None
    user: Optional[str] = None
    sources: Optional[str] = None


class RetrievalResponse(BaseModel):
    question: str
    sources: List[RAGSource]
