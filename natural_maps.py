import streamlit as st
import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
import folium
from streamlit_folium import st_folium
import pydeck as pdk

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

st.title("Natural Maps")

####

# Text input for place name
place_name = st.text_input(
    "Location",
    value="Augsburger Strasse, Berlin",
)
st.session_state.place_name = place_name
st.session_state.gdf = st_functions.name_to_gdf(place_name)

# Create a folium map
m = st_functions.map_location(st.session_state.gdf)


def add_markers_to_map(m, points):
    for point in points:
        point.add_to(m)
    return m


# Columns
left, right = st.columns((1, 2), gap="small")

# Left: Map
with left:
    # Add any user-generated geometry
    if "points" in st.session_state:
        st.markdown(st.session_state.points)
        add_markers_to_map(m, st.session_state.points)

    st_data = st_folium(m)

# Right: Chat/Explore
with right:
    explore_data(st_data)


st.header("Natural language input")
natural_input = st.text_area(
    "What would you like to know?",
    placeholder="eg. Find all public fountains in Berlin that are within a 200m radius of an ice cream shop.",
)
b = st.button("Translate to Overpass Query")
st.header("Generated query")
st.markdown(
    """
    - #Todo: Test a zero-shot with a pretrained LLM
    - #Todo: Finetune
    """
)
ice_cream_query = """
    [out:json];
    // fetch area “Berlin” to search in
    area["name"="Berlin"]->.searchArea;
    // gather results for: “amenity=fountain”
    (
    node["amenity"="fountain"](area.searchArea);
    way["amenity"="fountain"](area.searchArea);
    relation["amenity"="fountain"](area.searchArea);
    );
    // gather results for: “amenity=ice_cream”
    (
    node["amenity"="ice_cream"](area.searchArea);
    way["amenity"="ice_cream"](area.searchArea);
    relation["amenity"="ice_cream"](area.searchArea);
    );
    // print results
    out body;
    >;
    out skel qt;
    """

st.info(ice_cream_query)

st.markdown(
    """
    This query will return a .json file with all the fountains and ice cream shops in Berlin. 
    One would then need to process the results and make additional queries to find nearby fountains for each ice cream shop.
    """
)
run_query = st.button("Run query")

st.header("Run Query and do something")
st.markdown(
    "running the above query will return a json file, upon which it might be necessary to perform further operations"
)
if run_query:
    query_result = st_functions.overpass_query(ice_cream_query)
    st.info(query_result)

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

st.markdown(
    "A Portfolio project by J. Adam Hughes, Pasquale Zito and Justin Zarb as part of Data Science Retreat. [Github Repo](https://github.com/JustinZarb/shade-calculator)"
)
