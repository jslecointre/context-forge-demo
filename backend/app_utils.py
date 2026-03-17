import asyncio
import base64
import json
from typing import Dict, Optional
from fastapi import Request
from langgraph.graph.state import CompiledStateGraph
import os
from typing import List
from langchain_chroma.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_ibm import WatsonxEmbeddings

from backend import PROJECT_ROOT

from backend.agents.states.qa_states import RAGSource
from backend.logger import logger


TAG_TO_MESSAGE_TYPE = {
    "qa_wikipedia_message": "qa_wikipedia_message",
    "qa_simple_message": "qa_simple_message",
    "qa_final_message": "qa_final_message",
}


CUSTOM_EVENT_TYPES = ["tool_call_request"]


def format_sources_for_prompt(sources: List[RAGSource]) -> str:
    """Format RAGSources into a string for use in prompts.

    Args:
        sources: List of RAGSource objects.

    Returns:
        str: Formatted string with passages and metadata.
    """
    if len(sources) == 0:
        return "----- NO DATA - you don't have enough content to answer ----- "
    formatted_passages = []
    for i, source in enumerate(sources, 1):
        passage = f"""[Passage {i}]
Title: {source.title}
Source: {source.url}
Content:
{source.text}
"""
        formatted_passages.append(passage)

    return "\n---\n".join(formatted_passages)


def db_invocation(index_name: str = "langchain") -> Chroma:
    """Create and return an ElasticsearchStore instance for a given index.

    :param str index_name: name for the elasticsearch index.
    :return ElasticsearchStore: elasticsearch index.
    """
    DB_DIR = f"{PROJECT_ROOT}/{os.getenv('VDB_DIR', 'store')}"
    embed_params = {}
    embeddings = WatsonxEmbeddings(
        model_id="intfloat/multilingual-e5-large",
        url=os.getenv("WATSONX_URL"),
        project_id=os.getenv("WATSONX_PROJECT_ID"),
        params=embed_params,
    )

    vdb = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name=index_name,
    )
    return vdb


def doc2ragsource(doc: Document, score: float) -> RAGSource:
    """Convert a LangChain Document to a RAGSource.

    Args:
        doc: A LangChain Document object with page_content and metadata.

    Returns:
        RAGSource: A RAGSource object with mapped fields.
    """
    source_path = doc.metadata.get("source", "")
    # Extract title from first line of content or use filename
    first_line = doc.page_content.split("\n")[0].strip() if doc.page_content else ""
    title = first_line if first_line else os.path.basename(source_path)

    return RAGSource(
        url=source_path,
        text_llm=doc.page_content,
        text=doc.page_content,
        title=title,
        id=doc.id if hasattr(doc, "id") else None,
        score=score,
    )


def doc2ragsources(documents: List) -> List[RAGSource]:
    """Convert a list of LangChain Documents to a list of RAGSources.

    Args:
        documents: List of LangChain Document objects.

    Returns:
        List[RAGSource]: List of RAGSource objects.
    """
    return [doc2ragsource(doc, score) for doc, score in documents]


def get_workflows(request: Request) -> Dict:
    return request.app.state.workflows


def get_langchain_callbacks(request: Request) -> Dict:
    return request.app.state.callbacks


def get_authenticated_user(request: Request) -> Optional[str]:
    """
    Extracts the username from a Basic Auth Authorization header.
    Returns None if no valid Basic Auth credentials are found.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return None

    try:
        encoded_part = auth_header[len("Basic ") :]
        decoded = base64.b64decode(encoded_part).decode("utf-8")

        # Basic auth format is username:password
        if ":" not in decoded:
            return None

        username, _ = decoded.split(":", 1)
        return username.strip() if username else None
    except Exception:
        return None


async def event_generator(
    input_dictionary: Optional[Dict],
    workflow_runnable: CompiledStateGraph,
    config: RunnableConfig,
    query: str,
    thread_id: str,
    user: Optional[str] = None,
):
    """
    Wrapper around event_generator that collects the response and writes to database.

    Args:
        input_dictionary: Optional dictionary containing input data for the workflow.
        workflow_runnable: Compiled LangGraph state graph to execute and stream events from.
        config: RunnableConfig for the workflow execution.
        query: The original query string.
        thread_id: The thread ID for this conversation.
        user: Optional user identifier.

    Yields:
        str: SSE-formatted event strings.
    """
    collected_content = []

    async for event in workflow_runnable.astream_events(
        version="v2", input=input_dictionary, config=config, subgraphs=True
    ):
        kind = event["event"]
        tags = event.get("tags", [])
        print(f"{kind} {tags}")
        if kind == "on_chat_model_stream":
            logger.debug(f"[on_chat_model_stream] catch event tags {tags}")
            content = event["data"]["chunk"].content
            collected_content.append(content)
            for tag in tags:
                if tag in TAG_TO_MESSAGE_TYPE:
                    logger.debug(f"[on_chat_model_stream] send event {tag}")
                    data = json.dumps(
                        {
                            "type": TAG_TO_MESSAGE_TYPE[tag],
                            "message": content,
                            "content": content,
                        }
                    )
                    yield f"data:{data}\n\n"
                    await asyncio.sleep(0.1)
                    break

        elif kind == "on_custom_event":
            logger.debug(f'[on_custom_event] catch event {event["name"]}')
            if event["name"] in CUSTOM_EVENT_TYPES:
                data = json.dumps(
                    {
                        "type": event["name"],
                        "message": event["data"],
                    }
                )
                logger.debug(f'[on_custom_event] send event {event["name"]}')
                yield f"data:{data}\n\n"
                await asyncio.sleep(0.1)
