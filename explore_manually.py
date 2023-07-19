import streamlit as st

st.set_page_config(
    page_title=None,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None,
)
import folium
from streamlit_folium import st_folium
import src.streamlit_functions as st_functions
from src.st_explore_with_wordcloud import generate_wordcloud, explore_data
import pandas as pd

if "circles" not in st.session_state:
    st.session_state.circles = None

if "st_data" not in st.session_state:
    st.session_state.st_data = None

# Text input for place name
st.session_state.place_name = st.text_input(
    "Location",
    value="Theresienstrasse, Munich",
)
st.session_state.gdf = st_functions.name_to_gdf(st.session_state.place_name)

# Columns
explore_left, explore_right = st.columns((1, 2), gap="small")
# Left: Map
with explore_left:
    m = st_functions.update_map()  # folium.Map()
    st.session_state.st_data = st_folium(
        m, width=400, height=400, feature_group_to_add=st.session_state.circles
    )

# Right: Chat/Explore
with explore_right:
    if (st.session_state.st_data) and (st.session_state.st_data["zoom"] >= 13):
        # Initialize the checkbox value in the session state if it's not already set
        if "show_tags" not in st.session_state:
            st.session_state.show_tags = False

        def toggle_show_tags():
            st.session_state.show_tags = not (st.session_state.show_tags)

        # Use the session state value for the checkbox
        if not st.session_state.show_tags:
            st.button(label=f"Show tags", on_click=toggle_show_tags)
        else:
            st.button(label=f"Hide tags", on_click=toggle_show_tags)

        # Create a checkbox that will control whether the map and data are stored in the session state
        if st.session_state.explore_area:
            # check if  m and st_data already exist in the session state
            if "st_data_freeze" in st.session_state:
                # st_data already in session state
                pass
            else:
                # Store the map and data in the session state
                st.session_state["st_data_freeze"] = st.session_state.st_data
                # get bbox
                st.session_state["bbox"] = st_functions.bbox_from_st_data(
                    st.session_state.st_data_freeze
                )
                # query all nodes with tags in bbox
                st.session_state["nodes"] = st_functions.get_nodes_with_tags_in_bbox(
                    st.session_state.bbox
                )
                # get the tag content as a dictionary
                st.session_state["tags_in_bbox"] = st_functions.count_tag_frequency_old(
                    st.session_state.nodes
                )

            # show a wordcloud of amenities in the search area
            generate_wordcloud()

            # Multiselect options from the currently selected tag
            if "multiselected_options" not in st.session_state:
                st.session_state.multiselected_options = []

            st.multiselect(
                "Add items to map:",
                options=st.session_state.value_frequency.keys(),
                key="multiselected_options",
            )

            # Dictionary of key:value pairs where the keys are a tag key and the value are different tag values
            st.session_state.mask = {
                st.session_state.selected_key: st.session_state.multiselected_options
            }
            # filter the nodes in the bounding box which match the mask
            st.session_state.selected_nodes = st_functions.filter_nodes_with_tags(
                st.session_state.nodes, st.session_state.mask
            )
            ## Create colored circles for each of the above nodes
            st.session_state.circles = st_functions.create_circles_from_node_dict(
                st.session_state.selected_nodes
            )
            # Reset the checkbox
            st.session_state.add_selection = False
            st_functions.update_map()

        else:
            # delete
            temporary_variables = [
                "gdf",
                "m",
                "st_data_freeze",
                "bbox",
                "tags_in_bbox",
                "nodes",
            ]
            for var in temporary_variables:
                if var in st.session_state:
                    del st.session_state[var]

    else:
        st.markdown("Zoom in to see what's in the map")


if ("selected_nodes" in st.session_state) and st.session_state.selected_nodes:
    st.subheader("Currently shown on map:")
    for key, value in st.session_state.selected_nodes.items():
        st.markdown(f"{key}")
        df = pd.json_normalize(value, sep="\n")
        st.table(df)
