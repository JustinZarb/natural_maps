import folium
import streamlit as st
from streamlit_folium import folium_static, st_folium
import dev.streamlit_functions as st_functions

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

# Create a folium map
m = st_functions.map_location(st.session_state.gdf)

# Columns
left, right = st.columns((1, 2), gap="small")

with left:
    # Display the map
    if "s_points" in st.session_state:
        for p in st.session_state.s_points:
            p.add_to(m)
    st_folium(m)

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
        tags = {"amenity": st.session_state.selected_values}
        st.markdown(tags)
        selection = st_functions.filter_nodes_with_tags(st.session_state.nodes, tags)

        st.session_state.s_points = st_functions.folium_circles_from_bbox_tags(
            bbox=st.session_state.bbox,
            tags=tags,
        )
