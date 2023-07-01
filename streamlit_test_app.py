import streamlit as st
import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
import folium
from streamlit_folium import st_folium
import pydeck as pdk

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


# st.title("Echo Bot")

# # Initialize chat history
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Display chat messages from history on app rerun
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # React to user input
# if prompt := st.chat_input("What is up?"):
#     # Display user message in chat message container
#     st.chat_message("user").markdown(prompt)
#     # Add user message to chat history
#     st.session_state.messages.append({"role": "user", "content": prompt})

# response = f"Echo: {prompt}"
# # Display assistant response in chat message container
# with st.chat_message("assistant"):
#     st.markdown(response)
# # Add assistant response to chat history
# st.session_state.messages.append({"role": "assistant", "content": response})

api_key = os.getenv("OPENAI_KEY")
# overpass_query = OverpassQuery(api_key)
# user_input = "Find bike parking near tech parks in Kreuzberg, Berlin."
# result = overpass_query.process_user_input(user_input)

import streamlit as st
import openai

from dev.langchain.chains_as_classes_with_json import OverpassQuery
from dev.prompts.naturalmaps_bot import ChatBot

st.title("ChatGPT-like clone")

# Set OpenAI API key from Streamlit secrets
openai.api_key = api_key  # st.secrets["OPENAI_API_KEY"]

overpass_query = OverpassQuery(api_key)
chatbot = ChatBot()


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # message_placeholder = st.empty()
        chatbot.add_user_message(prompt)
        response = chatbot.run_conversation()
        st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
