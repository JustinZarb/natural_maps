import streamlit as st
import dev.streamlit_functions as st_functions
import pandas as pd

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

st.title("Natural Maps")
st.markdown(
    "A Portfolio project by J. Adam Hughes, Pasquale Zito and Justin Zarb as part of Data Science Retreat. [Github Repo](https://github.com/JustinZarb/shade-calculator)"
)
place_name = st.text_input(
    "Location",
    value="Charlottenburg, Charlottenburg-Wilmersdorf, Berlin, Germany",
)

left, right = st.columns((1, 2), gap="small")


with left:
    st_data = st_functions.map_location(place_name)
    current_bbox = st_functions.bbox_from_st_data(st_data["bounds"])

    # Check if 'bbox' is in the session state
    if "bbox" in st.session_state:
        # Check if the current bbox is different from the previous bbox
        if st.session_state.bbox != current_bbox:
            # reset get_keys if it has been set to True
            if "get_keys" in st.session_state:
                st.session_state.get_keys = False
            st.session_state.bbox = current_bbox
    else:
        # If 'bbox' is not in the session state, add it
        st.session_state.bbox = current_bbox

    # st.markdown(st_osmnx.get_tags(place_name, tags={"leisure": "park"}))
    # st_osmnx.plot_network(place_name)

with right:
    st.text(st.session_state.bbox)

    data = st.empty()
    tags_in_box = st.empty()

    get_keys = st.checkbox(
        label="Need inspiration? Check this box to see common tags in this area",
        key="get_keys",
    )
    if get_keys:
        data = st_functions.get_unique_tags_in_bbox(st.session_state.bbox)
        st.session_state.bbox_data = data
        st.session_state.tags_in_bbox = st_functions.count_tag_frequency(data)

        # wordcloud tags
        st.subheader("Tags in this area")
        tags_wordcloud = st_functions.generate_wordcloud(st.session_state.tags_in_bbox)
        st.image(tags_wordcloud.to_array(), use_column_width=True)

        st.selectbox(
            label="select a key",
            options=st.session_state.tags_in_bbox.keys(),
            key="tag_key",
        )

        if "tag_key" in st.session_state:
            value_frequency = st_functions.count_tag_frequency(
                data, tag=st.session_state.tag_key
            )
            values_wordcloud = st_functions.generate_wordcloud(value_frequency)
            st.subheader(f"top values for {st.session_state.tag_key}")
            st.image(values_wordcloud.to_array(), use_column_width=True)

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
