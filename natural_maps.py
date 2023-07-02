import streamlit as st

import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
from dev.function_calls.naturalmaps_bot import ChatBot
from streamlit_folium import st_folium
from config import OPENAI_API_KEY

import streamlit as st
from streamlit_chat import message
from streamlit_extras.colored_header import colored_header
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

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
    colored_header(label="", description="", color_name="blue-30")
    response_container = st.container()

    def get_text():
        autofill = st.button(label="autofill")
        if autofill:
            input = "Find all the ping pong tables in Monbijoupark"
        else:
            input = ""
        input_text = st.text_input("You: ", value=input, key="human_prompt")

        return input_text

    ## Applying the user input box
    with input_container:
        user_input = get_text()

    bot = ChatBot(openai_api_key=OPENAI_API_KEY)

    with response_container:
        if user_input:
            user_message = st.chat_message("user", avatar="👤")
            user_message.write(st.session_state.human_prompt)

            bot.add_user_message(st.session_state.human_prompt)
            bot.run_conversation()
            try:
                assistant_message = st.chat_message("assistant", avatar="🗺️")
                assistant_message.write(bot.latest_message)
            except:
                pass

        plan = False
        if plan:
            planner_message = st.chat_message("planner", avatar="📝")
            planner_message.write(bot.plan)


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
        if "circles" in st.session_state:
            circles = st.session_state.circles
            st.markdown(circles)
        else:
            circles = None
        st_data = st_folium(m)
        st.markdown(st_data)

    # Right: Chat/Explore
    with explore_right:
        explore_data(st_data)


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
