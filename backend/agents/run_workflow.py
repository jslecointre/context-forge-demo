import asyncio
import time
import uuid
import os
from backend.agents.qa_workflows import QAWorkflow
from backend.utils import to_bool


async def generate_main(
    question: str, selected_workflow: str = "agent_assist_agentic_workflow"
):
    """Main script to test LangGraph graphs outside of the FastAPI backend.

    This function allows for direct testing and execution of LangGraph workflows
    without going through the FastAPI application. LangSmith or LangFuse can be
    used for observability by configuring the appropriate callbacks or tracers.

    Args:
        question: The question to be processed by the workflow.
        selected_workflow: The name of the workflow to use. Defaults to "agent_assist_agentic_workflow".

    Returns:
        The result state from the compiled workflow execution.
    """
    with_context_forge = to_bool(os.getenv("WITH_CONTEXT_FORGE"))
    print(os.getenv("WITH_CONTEXT_FORGE"), with_context_forge)
    input = {"query": question}

    thread_id = f"{uuid.uuid4()}"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "recursion_limit": 100,
            "context_forge": with_context_forge,
        },
        "run_name": f'{selected_workflow}_workflow_{time.strftime("%m-%d-%Hh%M", time.localtime())}',
    }
    workflow = QAWorkflow()
    compiled_workflow = workflow.build_graph(
        checkpointer=None, draw=False, workflow_name=selected_workflow
    )
    result = await compiled_workflow.ainvoke(input=input, config=config)
    return result


workflow = QAWorkflow()
agent_assist_agentic_workflow = workflow.build_graph(
    checkpointer=None, draw=False, workflow_name="agent_assist_agentic_workflow"
)
agent_assist_mcp_agentic_workflow = workflow.build_graph(
    checkpointer=None, draw=False, workflow_name="agent_assist_mcp_agentic_workflow"
)

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    question = "would Lea Kim be eligible for live insurance considering her medical condition?"

    # workflow_name = "agent_assist_agentic_workflow"
    workflow_name = "agent_assist_mcp_agentic_workflow"
    # === RUN ASYNC WORKFLOW ===
    workflow_state = asyncio.run(
        generate_main(question=question, selected_workflow=workflow_name)
    )
    workflow_dict = dict(workflow_state)
