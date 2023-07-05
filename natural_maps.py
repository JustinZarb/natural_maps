import streamlit as st

# Must be the first command used on an app page
st.set_page_config(
    page_title=None,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None,
)

import dev.streamlit_functions as st_functions
from streamlit_folium import st_folium
from config import OPENAI_API_KEY
import pandas as pd
import numpy as np
import folium
from dev.naturalmaps_bot import ChatBot

prompts = pd.read_csv("./dev//prompts/prompts.csv")
prompt_type = prompts.promptType.unique()
basic_queries = prompts.loc[prompts["promptType"] == "Basic Query", "prompt"]

# This is just some random initialization data for the default image
pingpong = '{"version": 0.6, "generator": "Overpass API 0.7.60.6 e2dc3e5b", "osm3s": {"timestamp_osm_base": "2023-06-29T15:35:14Z", "timestamp_areas_base": "2023-06-29T12:13:45Z", "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."}, "elements": [{"type": "node", "id": 6835150496, "lat": 52.5226885, "lon": 13.3979877, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150497, "lat": 52.5227083, "lon": 13.3978939, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150598, "lat": 52.5229822, "lon": 13.3965893, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}, {"type": "node", "id": 6835150599, "lat": 52.5229863, "lon": 13.3964894, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}]}'
toilets = '{"version": 0.6, "generator": "Overpass API 0.7.60.6 e2dc3e5b", "osm3s": {"timestamp_osm_base": "2023-06-22T13:12:02Z", "timestamp_areas_base": "2023-06-11T03:07:17Z", "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."}, "elements": [{"type": "node", "id": 10811509225, "lat": 46.9422137, "lon": 7.4341902, "tags": {"amenity": "toilets"}}]}'
fg = st_functions.overpass_to_circles(pingpong)
bounds = fg.get_bounds()

# Parameters for the default image
if "center" not in st.session_state:
    st.session_state.center = st_functions.calculate_center(bounds)
if "feature_group" not in st.session_state:
    st.session_state["feature_group"] = fg
if "zoom" not in st.session_state:
    st.session_state["zoom"] = st_functions.calculate_zoom_level(bounds)


# Functions
def generate_prompt():
    if st.session_state.autofill:
        input = basic_queries[np.random.randint(len(basic_queries))]
    else:
        input = ""
    st.session_state.human_prompt = input


def get_text():
    st.text_input(
        "Ask the map! ",
        key="human_prompt",
        # value="Are there ping pong tables in Monbijoupark?",
    )
    st.checkbox(
        label="Use a random basic prompt", on_change=generate_prompt, key="autofill"
    )


def toggle_run():
    # Run the model reloads the app
    if "true_run" in st.session_state:
        st.session_state.true_run = st.session_state.run_checkbox
    else:
        st.session_state.true_run = True
        if st.session_state.human_prompt:
            st.session_state.bot = ChatBot(openai_api_key=OPENAI_API_KEY)


# Start of page
st.title("Natural Maps")
st.markdown(
    """J. Adam Hughes,
Justin Zarb, Pasquale Zito"""
)

# Layout of input/response containers
map_container = st.container()
input_container = st.container()
response_container = st.container()

with map_container:
    m = folium.Map()
    st_data = st_folium(
        m,
        feature_group_to_add=st.session_state.feature_group,
        center=st.session_state.center,
        zoom=st.session_state.zoom,
        width=1200,
        height=500,
    )
    st.session_state.bbox = st_functions.bbox_from_st_data(st_data)

## Applying the user input box
with input_container:
    input = get_text()
    if ("user_input" in st.session_state) and (st.session_state.user_input == input):
        pass
    else:
        st.session_state.user_input = input

    st.checkbox(
        "Run plan and execute-style agent using GPT 3.5",
        on_change=toggle_run,
        key="run_checkbox",
    )

with response_container:
    if st.session_state.human_prompt:
        st.session_state.bot = ChatBot(openai_api_key=OPENAI_API_KEY)
        if ("true_run" in st.session_state) and (st.session_state.true_run):
            # display the user's message in the chat
            user_message = st.chat_message("user", avatar="👤")
            user_message.write(st.session_state.human_prompt)
            # Initialise and run the bot
            st.session_state.bot.add_user_message(st.session_state.human_prompt)
            st.session_state.bot.run_conversation_streamlit(
                num_iterations=8, temperature=0.2
            )

            # update parameters for map
            st.session_state.true_run = False


if "gdf" in st.session_state:
    st.markdown(st.session_state.gdf)


st.markdown(
    """
NaturalMaps is an attempt to explore maps with natural language, 
such as “Find all the quietest coffee shops in Berlin that open before 
8 AM and are in close proximity to a library.” At the moment, this is 
readily accessible open data, but going beyond simple queries requires 
expert know-how. We are exploring ways to make this information and 
analysis more accessible to the user. \n Naturalmaps is a portfolio project by J. Adam Hughes, Justin Zarb 
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
