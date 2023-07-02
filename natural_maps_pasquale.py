import streamlit as st

import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
import folium
from streamlit_folium import st_folium

import os

# import json
# import pandas as pd
# import requests
# from time import gmtime, strftime
# from langchain.prompts import PromptTemplate
# from langchain.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
# from langchain.chains import LLMChain
# from langchain.chains import (
#     TransformChain,
#     LLMChain,
#     SimpleSequentialChain,
#     SequentialChain,
# )
# import streamlit as st
# import openai

from dev.langchain.chains_as_classes_with_json import OverpassQuery
from dev.prompts.naturalmaps_bot import ChatBot

# from config import OPENAI_API_KEY
api_key = os.getenv("OPENAI_KEY")

# overpass_query = OverpassQuery(api_key)
# user_input = "Find bike parking near tech parks in Kreuzberg, Berlin."
# result = overpass_query.process_user_input(user_input)

# Set OpenAI API key from Streamlit secrets
openai.api_key = api_key  # st.secrets["OPENAI_API_KEY"]

# We've got two bots at our disposal, for the moment
overpass_query = OverpassQuery(api_key)
chatbot = ChatBot()


if "messages" not in st.session_state:
    st.session_state.messages = []


st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

# This is just some random initialization data
data_str = '{"version": 0.6, "generator": "Overpass API 0.7.60.6 e2dc3e5b", "osm3s": {"timestamp_osm_base": "2023-06-29T15:35:14Z", "timestamp_areas_base": "2023-06-29T12:13:45Z", "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."}, "elements": [{"type": "node", "id": 6835150496, "lat": 52.5226885, "lon": 13.3979877, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150497, "lat": 52.5227083, "lon": 13.3978939, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150598, "lat": 52.5229822, "lon": 13.3965893, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}, {"type": "node", "id": 6835150599, "lat": 52.5229863, "lon": 13.3964894, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}]}'
fg = st_functions.overpass_to_feature_group(data_str)
bounds = fg.get_bounds()

if "center" not in st.session_state:
    st.session_state.center = st_functions.calculate_center(bounds)
if "feature_group" not in st.session_state:
    st.session_state["feature_group"] = fg
if "zoom" not in st.session_state:
    st.session_state["zoom"] = st_functions.calculate_zoom_level(bounds)


st.title("Natural Maps")

# Explore the data manually
with st.expander("Manually explore a map area"):
    # Text input for place name
    place_name = st.text_input(
        "Location",
        value="Berlin",
    )
    st.session_state.place_name = place_name
    st.session_state.gdf = st_functions.name_to_gdf(place_name)

    # Columns
    explore_left, explore_right = st.columns((1, 2), gap="small")
    # Left: Map
    with explore_left:
        m = st_functions.update_map()
        # for lat, lon, tags in node_data:
        #     tags_content = "<br>".join([f"<b>{k}</b>: {v}" for k, v in tags.items()])
        #     folium.Marker(location=[lat, lon], popup=tags_content).add_to(m)
        st_data = st_folium(m)

    # Right: Chat/Explore
    with explore_right:
        explore_data(st_data)

# Talk to the map!
st.subheader("Natural language input")


bot_left, bot_right = st.columns((1, 2), gap="small")

# if bot_left.button("Shift center"):
#     random_shift_y = (random.random() - 0.5) * 0.3
#     random_shift_x = (random.random() - 0.5) * 0.3
#     st.session_state["center"] = [
#         st.session_state["center"][0] + random_shift_y,
#         st.session_state["center"][1] + random_shift_x,
#     ]

# if bot_left.button("Shift and zoom"):
#     st.session_state["center"] = (49.732399900000004, 10.41650145)
#     st.session_state["zoom"] = 7.280601066479868
# if bot_left.button("remove dots"):
#     st.session_state["feature_group"] = folium.FeatureGroup(
#         name="Elements from overpass"
#     )


with bot_left:
    m2 = folium.Map(
        height="100%",
    )
    st_folium(
        m2,
        feature_group_to_add=st.session_state.feature_group,
        center=st.session_state.center,
        zoom=st.session_state.zoom,
    )


with bot_right:
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

    # message = st.chat_message("assistant")
    # message.write("Hello human")
    # #message.bar_chart(np.random.randn(30, 3))

# st.session_state.center = (53.494239118767496, 13.329420089721681)

# out = st_folium(
#     m2,
#     feature_group_to_add=st.session_state.feature_group,
#     center=(53.494239118767496, 13.329420089721681),
#     zoom=st.session_state.zoom,
# )


st.markdown(
    """
NaturalMaps is an attempt to explore maps with natural language, 
such as “Find all the quietest coffee shops in Berlin that open before 
8 AM and are in close proximity to a library.” At the moment, this is 
readily accessible open data, but going beyond simple queries requires 
expert know-how. We are exploring ways to make this information and 
analysis more accessible to the user.

\n
Naturalmaps is a portfolio project by J. Adam Hughes, Justin Zarb 
and Pasquale Zito, developed as part of Data Science Retreat. 
[Github Repo](https://github.com/JustinZarb/shade-calculator)"""
)

st.header("How to use this tool")
st.markdown(
    """Open Street Map is awesome but hard to query. We are here to study what can
    be done and streamline the process of question -> query -> process -> output. 
    Here are some examples of how we imagine this to be used: 
    """
)
st.markdown(
    """
| Persona         | Description | Spatial Query |
|-----------------|-------------|---------------|
| Urban Athlete   | Enjoys staying active and exploring the city in a dynamic way. | Find all the parks in Berlin that have a running path of at least 5km and are within 500m of a public swimming pool for a post-run dip. |
| Hungry Partygoer | Enjoys the vibrant nightlife of the city and loves to eat late-night snacks. | Find all the late-night food spots that are within a 200m radius of nightclubs that are open until at least 3 AM. |
| City Planner | Interested in understanding and improving the urban layout of the city. | Find all residential buildings in Berlin that are more than 50m high and are not within 500m of any public park or green space. |
| Culture Seeker | Always looking to explore cultural heritage and history. | Find all the historic landmarks in Berlin that are within a 1km radius of an art gallery or museum. |
| Freelance Writer | Always in search of quiet spots to sit, observe, and pen their thoughts. | Find all the quietest coffee shops (at least 200m away from any main road) in Berlin that open before 8 AM and are in close proximity to a library or a bookstore. |

"""
)
