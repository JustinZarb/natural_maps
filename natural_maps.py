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
import pandas as pd
import numpy as np
from dev.function_calls.naturalmaps_bot import ChatBot
from streamlit_folium import st_folium
from config import OPENAI_API_KEY

prompts = pd.read_csv("./dev//prompts/prompts.csv")
prompt_type = prompts.promptType.unique()
basic_queries = prompts.loc[prompts["promptType"] == "Basic Query", "prompt"]

## Start of page
st.title("Natural Maps")
st.markdown(
    """a portfolio project by J. Adam Hughes,
Justin Zarb and Pasquale Zito, 
developed as part of Data Science Retreat."""
)

# Talk to the map!
st.subheader("Ask the map!")

bot_left, bot_right = st.columns((1, 2), gap="small")
with bot_left:
    m = st_functions.map_location(st_functions.name_to_gdf("berlin"))
    st_folium(m, key="bot_map")


with bot_right:
    # Layout of input/response containers
    input_container = st.container()
    response_container = st.container()

    def generate_prompt():
        if st.session_state.autofill:
            input = basic_queries[np.random.randint(len(basic_queries))]
        else:
            input = ""
        st.session_state.human_prompt = input

    def get_text():
        st.checkbox(
            label="Use a random basic prompt", on_change=generate_prompt, key="autofill"
        )
        st.text_input(
            "You: ",
            key="human_prompt",
            value="Are there ping pong tables in Monbijoupark?",
            disabled=st.session_state.autofill,
        )

    def toggle_run():
        if "true_run" in st.session_state:
            st.session_state.true_run = st.session_state.run_checkbox
        else:
            st.session_state.true_run = True

    ## Applying the user input box
    with input_container:
        input = get_text()
        if ("user_input" in st.session_state) and (
            st.session_state.user_input == input
        ):
            pass
        else:
            st.session_state.user_input = input
        st.checkbox("Run Model", on_change=toggle_run, key="run_checkbox")

    with response_container:
        st.markdown(
            [
                st.session_state.human_prompt,
                st.session_state.run_checkbox,
                ("true_run" in st.session_state),
                st.session_state.true_run,
            ]
        )

        if (st.session_state.run_checkbox) and (st.session_state.human_prompt):
            st.session_state.bot = ChatBot(openai_api_key=OPENAI_API_KEY)
            if ("true_run" in st.session_state) and (st.session_state.true_run):
                # display the user's message in the chat
                user_message = st.chat_message("user", avatar="👤")
                user_message.write(st.session_state.human_prompt)
                # Initialise and run the bot
                st.session_state.bot.add_user_message(st.session_state.human_prompt)
                st.session_state.bot.run_conversation_streamlit(num_iterations=5)
                st.session_state.true_run = False
            # for m in st.session_state["message_history"]:
            #   st.session_state.assistant_message.write(m)


st.header("Debug")
if "overpass_queries" in st.session_state:
    for task, query_dict in st.session_state.overpass_queries.items():
        st.markdown(task)
        st.markdown(query_dict)

st.multiselect(
    label="Feedback",
    options=["400 error", "empty result", "wrong key/value"],
    key="user_feedback",
    disabled=not ("true_run" in st.session_state),
)


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
