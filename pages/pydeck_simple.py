import streamlit as st
import dev.streamlit_functions as st_functions
import folium
from streamlit_folium import st_folium
import pandas as pd
from IPython.display import display
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk


st.set_page_config(
    page_title="Naturalmaps_pydeck",
    page_icon=":world_map:️",
    layout="wide",
)

st.title("Natural Maps")


# Columns
left, right = st.columns((1, 2), gap="small")
with left:
    # get zoom level
    initial_zoom = st_functions.calculate_zoom_level(st.session_state.gdf)
    # Create the map
    deck = st_functions.map_location_pydeck(st.session_state.gdf)
    # Create an empty placeholder
    map_placeholder = st.empty()
    # Display the map
    map_placeholder.pydeck_chart(deck)

with right:
    # Select some of these values to show on the map
    st.multiselect(
        "Items to show on map:",
        options=st.session_state.value_frequency.keys(),
        key="selected_values",
        default="bar",
    )

    if st.session_state.selected_values is not None:
        # show selected values on the map in different colors
        tags = {st.session_state.selected_key: st.session_state.selected_values}

        selection = st_functions.filter_nodes_with_tags(st.session_state.nodes, tags)
        # Pydeck
        layers = []
        for key, values in selection.items():
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    values,
                    get_position=["lon", "lat"],
                    get_radius=10,
                    get_fill_color=st_functions.word_to_color(key),
                    pickable=True,
                )
            )
