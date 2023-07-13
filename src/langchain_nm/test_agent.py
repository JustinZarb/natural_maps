from langchain import (
    LLMMathChain,
    OpenAI,
    SerpAPIWrapper,
    SQLDatabase,
    SQLDatabaseChain,
)
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

import os
import json
import pandas as pd
import requests
from time import gmtime, strftime

from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.chains import (
    TransformChain,
    LLMChain,
    SimpleSequentialChain,
    SequentialChain,
)

import os

# The standard name is OPEN_AI_KEY, shall we change it?
api_key = os.getenv("OPENAI_KEY")

from typing import Union

llm = ChatOpenAI(temperature=0, openai_api_key=api_key, model_name="gpt-3.5-turbo-0613")

chain_to_overpass_prompt = PromptTemplate(
    input_variables=["user_text_input"],
    template=""""Turn the user's message into an overpass QL query.
            Example prompt: "Find bike parking near tech parks in Kreuzberg, Berlin.":\n\n {user_text_input}""",
)

chain_to_overpass = LLMChain(
    llm=llm, prompt=chain_to_overpass_prompt, output_key="ql_query"
)


def overpass_query(ql_query):
    """Run an overpass query"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url, params={"data": ql_query})
    if response.content:
        try:
            data = response.json()
        except:
            data = {"error": str(response)}
    else:
        print("Empty response from Overpass API")
        data = {
            "warning": "received an empty response from Overpass API. Tell the user."
        }
    data_str = json.dumps(data)

    return data_str


# Apparently, TransformChain wants functions acting on dictionaries
# You can't directly use general functions
def transform_func(inputs: dict) -> dict:
    query_input = inputs["ql_query"]
    op_answer = overpass_query(query_input)
    return {"overpass_answer": op_answer}


transform_chain = TransformChain(
    input_variables=["ql_query"],
    output_variables=["overpass_answer"],
    transform=transform_func,
)

chain_to_user_prompt = PromptTemplate(
    input_variables=["overpass_answer", "user_text_input"],
    template=""""Answer the user's message {user_text_input} based on the result of an overpass QL query contained in {overpass_answer}.""",
)

chain_to_user = LLMChain(llm=llm, prompt=chain_to_user_prompt)


# Load the tool configs that are needed.
search = SerpAPIWrapper()
llm_math_chain = LLMMathChain(llm=llm, verbose=True)

tools = [
    Tool.from_function(
        func=chain_to_overpass.run,
        name="Translate to oeverpass QL",
        description="useful for when you need to turn text messages into overpass QL queries"
        # coroutine= ... <- you can specify an async method if desired as well
    ),
]


from langchain.chains.conversation.memory import ConversationBufferWindowMemory


# # initialize LLM (we use ChatOpenAI because we'll later define a `chat` agent)
# llm = ChatOpenAI(
#         openai_api_key="OPENAI_API_KEY",
#         temperature=0,
#         model_name='gpt-3.5-turbo'
# )

# initialize conversational memory
conversational_memory = ConversationBufferWindowMemory(
    memory_key="chat_history", k=5, return_messages=True
)

from langchain.agents import initialize_agent


# initialize agent with tools
agent = initialize_agent(
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    tools=tools,
    llm=llm,
    verbose=True,
    max_iterations=3,
    early_stopping_method="generate",
    memory=conversational_memory,
)

text = "are there any ping pong tables in Monbijoupark?"


llm = ChatOpenAI(
    temperature=0,
    model="gpt-3.5-turbo-0613",
    openai_api_key=api_key,
)

agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)


class CircumferenceTool(BaseTool):
    name = "Circumference calculator"
    description = "use this tool when you need to calculate a circumference using the radius of a circle"

    def _run(self, radius: Union[int, float]):
        return float(radius) * 2.0 * pi

    def _arun(self, radius: int):
        raise NotImplementedError("This tool does not support async")
