import streamlit as st
import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
import folium
from streamlit_folium import st_folium
import pydeck as pdk
import osmnx as ox
import random

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)


data_str = '{"version": 0.6, "generator": "Overpass API 0.7.60.6 e2dc3e5b", "osm3s": {"timestamp_osm_base": "2023-06-29T15:35:14Z", "timestamp_areas_base": "2023-06-29T12:13:45Z", "copyright": "The data included in this document is from www.openstreetmap.org. The data is made available under ODbL."}, "elements": [{"type": "node", "id": 3690386818, "lat": 46.9418135, "lon": 7.4350152, "tags": {"leisure": "pitch", "sport": "table_tennis"}}, {"type": "node", "id": 6835150496, "lat": 52.5226885, "lon": 13.3979877, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150497, "lat": 52.5227083, "lon": 13.3978939, "tags": {"leisure": "pitch", "sport": "table_tennis", "wheelchair": "yes"}}, {"type": "node", "id": 6835150598, "lat": 52.5229822, "lon": 13.3965893, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}, {"type": "node", "id": 6835150599, "lat": 52.5229863, "lon": 13.3964894, "tags": {"access": "customers", "leisure": "pitch", "sport": "table_tennis"}}]}'

data = folium.GeoJson(data_str).data

nodes = data["elements"]
node_data = [(node["lat"], node["lon"], node["tags"]) for node in nodes]


# for coords in node_coordinates:
#     folium.Marker(location=coords).add_to(m)

fg = folium.FeatureGroup(name="Elements from overpass")
# fg.add_child(folium.features.GeoJson(bounds))


# for capital in capitals.itertuples():
#     fg.add_child(
#         folium.Marker(
#             location=[capital.latitude, capital.longitude],
#             popup=f"{capital.capital}, {capital.state}",
#             tooltip=f"{capital.capital}, {capital.state}",
#             icon=folium.Icon(color="green")
#             if capital.state == st.session_state["selected_state"]
#             else None,
#         )
#     )
for lat, lon, tags in node_data:
    tags_content = "<br>".join([f"<b>{k}</b>: {v}" for k, v in tags.items()])
    fg.add_child(folium.Marker(location=[lat, lon], popup=tags_content))

# fg.add_child(bounds = {'_southWest': {'lat': 52.494239118767496, 'lng': 13.329420089721681}, '_northEast': {'lat': 52.50338318818063, 'lng': 13.344976902008058}})
# place = "Berlin, Germany"

if "center" not in st.session_state:
    st.session_state["center"] = (52.494239118767496, 13.329420089721681)
if "feature_group" not in st.session_state:
    st.session_state["feature_group"] = fg
if "zoom" not in st.session_state:
    st.session_state["zoom"] = 10

# st.session_state.feature_group = fg
# st.session_state.zoom = 10
# st.session_state.gdf = ox.geocode_to_gdf(place)
# st.session_state.center = (52.494239118767496, 13.329420089721681)
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

if bot_left.button("Shift center"):
    random_shift_y = (random.random() - 0.5) * 0.3
    random_shift_x = (random.random() - 0.5) * 0.3
    st.session_state["center"] = [
        st.session_state["center"][0] + random_shift_y,
        st.session_state["center"][1] + random_shift_x,
    ]

if bot_left.button("Shift and zoom"):
    st.session_state["center"] = (49.732399900000004, 10.41650145)
    st.session_state["zoom"] = 7.280601066479868
if bot_left.button("remove dots"):
    st.session_state["feature_group"] = folium.FeatureGroup(
        name="Elements from overpass"
    )


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
    import numpy as np

    message = st.chat_message("assistant")
    message.write("Hello human")
    message.bar_chart(np.random.randn(30, 3))

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


test = []
for lat, lon, tags in node_data:
    tags_content = "<br>".join([f"<b>{k}</b>: {v}" for k, v in tags.items()])
    test.append((lat, lon, tags_content))
