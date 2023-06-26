import streamlit as st
import dev.streamlit_functions as st_functions
import folium
from streamlit_folium import st_folium
import pandas as pd
from IPython.display import display

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)


st.title("Natural Maps")

# Text input for place name
place_name = st.text_input(
    "Location",
    value="Augsburger Strasse, Berlin",
)

# Initialize session state if it doesn't exist
st.session_state.gdf = st_functions.name_to_gdf(place_name)
st.session_state.feature_group = folium.FeatureGroup(name="points")

# create a placeholder
feature_placeholder = st.empty()
feature_placeholder.pydeck_chart = st.session_state.feature_group

# Columns
left, right = st.columns((1, 2), gap="small")
with left:
    # Create the map
    m = st_functions.map_location(st.session_state.gdf)

    # Display the map
    st_data = st_folium(m, feature_group_to_add=feature_placeholder)


with right:
    if st_data["zoom"] >= 13:
        st.checkbox(label=f"Common tags in this view", value=True, key="get_keys")
        # Create a checkbox that will control whether the map and data are stored in the session state
        if st.session_state.get_keys:
            # check if  m and st_data already exist in the session state
            if "m" in st.session_state:
                pass
            else:
                # If the checkbox is checked, store the map and data in the session state
                st.session_state["m"] = m
                st.session_state["st_data"] = st_data
                st.session_state["bbox"] = st_functions.bbox_from_st_data(
                    st.session_state.st_data["bounds"]
                )
                st.session_state["nodes"] = st_functions.get_nodes_with_tags_in_bbox(
                    st.session_state.bbox
                )
                st.session_state["tags_in_bbox"] = st_functions.count_tag_frequency(
                    st.session_state.nodes
                )

            st.subheader("Tags in this area")
            st.markdown(st.session_state.bbox)
            tag_keys = list(st.session_state.tags_in_bbox.keys())
            default_key_index = (
                tag_keys.index("amenity") if "amenity" in tag_keys else 0
            )
            # Select a tag key for wordcloud visualisation
            st.selectbox(
                label="Select a different tag",
                options=st.session_state.tags_in_bbox.keys(),
                index=default_key_index,
                key="selected_key",
            )
            # Return a dictionary with the frequency each value appears in the bounding box
            st.session_state.value_frequency = st_functions.count_tag_frequency(
                st.session_state.nodes, tag=st.session_state.selected_key
            )

            # Generate word cloud
            values_wordcloud = st_functions.generate_wordcloud(
                st.session_state.value_frequency
            )
            st.subheader(f"Top {st.session_state.selected_key} values")
            st.image(values_wordcloud.to_array(), use_column_width=True)

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

                st.markdown(tags)

                points = st_functions.add_nodes_to_map(
                    m=st.session_state.m,
                    bbox=st.session_state.bbox,
                    tags=tags,
                )
                st.markdown(points)
                for p in points:
                    st.session_state.feature_group.add_child(p)

        else:
            # If the checkbox is unchecked, remove the map and data from the session state
            if "m" in st.session_state:
                del st.session_state["m"]
            if "st_data" in st.session_state:
                del st.session_state["st_data"]
            if "bbox" in st.session_state:
                del st.session_state["bbox"]
            if "tags_in_bbox" in st.session_state:
                del st.session_state["tags_in_bbox"]
            if "nodes" in st.session_state:
                del st.session_state["nodes"]

    else:
        st.markdown("Zoom in to see what's in the map")


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
