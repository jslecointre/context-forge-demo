# flake8: noqa: E501
from langchain_core.prompts import PromptTemplate

from backend.agents.chains import qa_model
from backend.agents.prompts import underwriting_knowledge_qa_prompt

qa_config = {"callbacks": [], "tags": ["qa_agent_message"]}

prompt = PromptTemplate(
    template=underwriting_knowledge_qa_prompt,
    input_variables=["tools_descriptions"],
)

agent_assist_qa_chain = prompt | qa_model.with_config(qa_config)
