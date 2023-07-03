import dev.streamlit_functions as st_functions
import streamlit as st
from streamlit_folium import st_folium
import folium

# This is just some random initialization data
data_str = '{"version": 0.6, "generator": "Overpass API 0.7.60.6 e2dc3e5b", "osm3s": {"timestamp_osm_base": "2023-06-29T15:35:14Z", "timestamp_areas_base": "2023-06-29T12:13:45Z", "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."}, "elements": [{"type": "node", "id": 6835150496, "lat": 52.5226885, "lon": 13.3979877, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150497, "lat": 52.5227083, "lon": 13.3978939, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150598, "lat": 52.5229822, "lon": 13.3965893, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}, {"type": "node", "id": 6835150599, "lat": 52.5229863, "lon": 13.3964894, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}]}'

# Here we define the feature_group, it contains all the mark points and tags
fg = st_functions.overpass_to_feature_group(data_str)
bounds = fg.get_bounds()

# Here we initialize the three session_state variables we will be interacting with in st_folium
if "center" not in st.session_state:
    st.session_state.center = st_functions.calculate_center(bounds)
if "feature_group" not in st.session_state:
    st.session_state["feature_group"] = fg
if "zoom" not in st.session_state:
    st.session_state["zoom"] = st_functions.calculate_zoom_level(bounds)


bot_left, bot_right = st.columns((1, 2), gap="small")
with bot_right:
    m = folium.Map(
        height="100%",
    )
    st_folium(
        m,
        feature_group_to_add=st.session_state.feature_group,
        center=st.session_state.center,
        zoom=st.session_state.zoom,
    )
