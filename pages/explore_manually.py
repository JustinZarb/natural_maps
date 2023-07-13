import streamlit as st

st.set_page_config(
    page_title=None,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None,
)
from streamlit_folium import st_folium
import src.streamlit_functions as st_functions
from src.st_explore_with_wordcloud import explore_data


# Explore the data manually

# Text input for place name
place_name = st.text_input(
    "Location",
    value="Museum Island",
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
    else:
        circles = None
    st_data = st_folium(m)

# Right: Chat/Explore
with explore_right:
    explore_data(st_data)
