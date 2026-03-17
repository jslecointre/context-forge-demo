import logging
import os
import time
import warnings
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from langfuse.langchain import CallbackHandler
from langgraph.checkpoint.memory import InMemorySaver

from backend import PROJECT_ROOT
from backend.agents.qa_workflows import QAWorkflow
from backend.app_utils import (
    event_generator,
    get_authenticated_user,
    get_langchain_callbacks,
    get_workflows,
    db_invocation,
    doc2ragsources,
)
from backend.logger import logger
from backend.schemas import (
    QARequestWithWorkflow,
    RetrievalResponse,
    SimpleQAResponse,
)
from backend.utils import verify_credentials

# Suppress Pydantic V2 migration warnings
warnings.filterwarnings("ignore", message="Valid config keys have changed in V2")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
# Add the parent directory to sys.path to make sure we can import from server

# Don't override parent logger settings
logger.propagate = True

# Silence uvicorn reload logs
logging.getLogger("uvicorn.supervisors.ChangeReload").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    frontend_path = os.path.join(PROJECT_ROOT, "frontend")
    if os.path.exists(frontend_path):
        app.mount("/site", StaticFiles(directory=frontend_path), name="frontend")
        logger.debug(f"Frontend mounted from: {frontend_path}")

        # Also mount the static directory directly for assets referenced as /static/
        static_path = os.path.join(frontend_path, "static")
        if os.path.exists(static_path):
            app.mount("/static", StaticFiles(directory=static_path), name="static")
            logger.debug(f"Static assets mounted from: {static_path}")
    else:
        logger.warning(f"Frontend directory not found: {frontend_path}")

    checkpointer = InMemorySaver()  # TODO use AsyncSqliteStore
    # checkpointer = None
    rag_workflow = QAWorkflow()
    agent_assist_agentic_workflow = rag_workflow.build_graph(
        checkpointer=checkpointer,
        draw=False,
        workflow_name="agent_assist_agentic_workflow",
    )
    agent_assist_mcp_agentic_workflow = rag_workflow.build_graph(
        checkpointer=checkpointer,
        draw=False,
        workflow_name="agent_assist_mcp_agentic_workflow",
    )

    app.state.workflows = {
        "agent_assist_agentic_workflow": agent_assist_agentic_workflow,
        "agent_assist_mcp_agentic_workflow": agent_assist_mcp_agentic_workflow,
    }
    app.state.callbacks = (
        [CallbackHandler()] if os.getenv("LANGFUSE_BASE_URL") else None
    )
    logger.info("lifespan started")
    yield
    logger.info("Q&A Application shutting down")


# App initialization
auth_enabled = os.getenv("BACKEND_AUTH", "false").lower() in ("1", "true", "yes")
local_secure = [Depends(verify_credentials)] if auth_enabled else []
app = FastAPI(lifespan=lifespan)

# Configure allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost:8002",  # Local development
    "http://127.0.0.1:8002",  # Local development alternative
    "*",  # Allow all origins for testing
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = os.path.join(PROJECT_ROOT, "frontend")

# Mount static directories
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(frontend_dir, "static")),
    name="static",
)
app.mount("/site", StaticFiles(directory=frontend_dir), name="site")


# Routes
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend HTML page."""
    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    index_path = os.path.join(frontend_dir, "index.html")
    logger.info("webUI")

    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="Frontend index.html not found")

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    broker_token = os.getenv("BROKER_CONTEXT_FORGE_TOKEN", "")
    analyst_token = os.getenv("ANALYST_CONTEXT_FORGE_TOKEN", "")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8002").rstrip("/")
    backend_user = os.getenv("BACKEND_USER", "user")
    backend_password = os.getenv("BACKEND_PASSWORD", "password")
    injected_script = (
        f"<script>\n"
        f"  window.BROKER_CONTEXT_FORGE_TOKEN = {broker_token!r};\n"
        f"  window.ANALYST_CONTEXT_FORGE_TOKEN = {analyst_token!r};\n"
        f"  window.BACKEND_URL = {backend_url!r};\n"
        f"  window.BACKEND_USER = {backend_user!r};\n"
        f"  window.BACKEND_PASSWORD = {backend_password!r};\n"
        f"</script>\n"
    )
    content = content.replace("</head>", injected_script + "</head>", 1)

    return HTMLResponse(content=content)


@app.post("/sources", response_model=RetrievalResponse, dependencies=local_secure)
async def get_sources(body: QARequestWithWorkflow) -> RetrievalResponse:
    query = body.query
    k = body.k
    vdb = db_invocation()
    # results = await vdb.asimilarity_search_with_score(query, k=k)
    results = await vdb.asimilarity_search_with_relevance_scores(query, k=k)
    processed_rag_sources = doc2ragsources(documents=results)
    response = RetrievalResponse(question=query, sources=processed_rag_sources)
    return response


@app.post("/stream_chat", response_model=SimpleQAResponse, dependencies=local_secure)
async def stream_response(
    body: QARequestWithWorkflow,
    request: Request,
    workflow=Depends(get_workflows),
    callbacks=Depends(get_langchain_callbacks),
):
    """Streaming endpoint returning events. Uses LangGraph graphs with various workflows."""
    query = body.query
    workflow_name = body.workflow
    context_forge = body.context_forge
    context_forge_token = body.context_forge_token

    raw_virtual_mcp = body.context_forge_virtual_mcp
    if raw_virtual_mcp == "broker_gateway":
        context_forge_virtual_mcp = os.getenv("BROKER_CONTEXT_FORGE_VSERVER")
    elif raw_virtual_mcp == "analysts_gateway":
        context_forge_virtual_mcp = os.getenv("ANALYST_CONTEXT_FORGE_VSERVER")
    else:
        context_forge_virtual_mcp = None

    persona = "broker" if raw_virtual_mcp == "broker_gateway" else "analyst"

    thread_id = body.thread_id
    workflow_runnable = workflow.get(workflow_name.value)
    thread_id = body.thread_id
    logger.info(f'Received query "{body.query}" for workflow "{workflow_name}" ')

    user = get_authenticated_user(request) if auth_enabled else None

    try:
        return StreamingResponse(
            event_generator(
                input_dictionary={"query": query, "error": False},
                config={
                    "configurable": {
                        "thread_id": thread_id,
                        "context_forge": context_forge,
                        "context_forge_token": context_forge_token,
                        "context_forge_virtual_mcp": context_forge_virtual_mcp,
                        "recursion_limit": 100,
                        "persona": persona,
                    },
                    "run_name": f'{workflow_name.value}_{time.strftime("%m-%d-%Hh%M", time.localtime())}',
                    "callbacks": callbacks,
                },
                workflow_runnable=workflow_runnable,
                query=query,
                thread_id=thread_id,
                user=user,
            ),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Error generating backend streaming response: {e}")
        raise HTTPException(status_code=500, detail=str(e))
