import dev.streamlit_functions as st_functions
import streamlit as st


def generate_wordcloud():
    st.subheader("Tags in this area")
    st.markdown(st.session_state.bbox)

    tag_keys = list(st.session_state.tags_in_bbox.keys())
    default_key_index = tag_keys.index("amenity") if "amenity" in tag_keys else 0

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
    values_wordcloud = st_functions.generate_wordcloud(st.session_state.value_frequency)
    st.subheader(f"Things tagged as '{st.session_state.selected_key}'")
    st.image(values_wordcloud.to_array(), use_column_width=True)


def explore_data(st_data):
    if st_data["zoom"] >= 13:
        st.checkbox(label=f"Common tags in this view", value=True, key="explore_area")
        # Create a checkbox that will control whether the map and data are stored in the session state
        if st.session_state.explore_area:
            # check if  m and st_data already exist in the session state
            if "st_data" in st.session_state:
                # st_data already in session state
                pass
            else:
                # Store the map and data in the session state
                st.session_state["st_data"] = st_data
                # get bbox
                st.session_state["bbox"] = st_functions.bbox_from_st_data(
                    st.session_state.st_data["bounds"]
                )
                # query all nodes with tags in bbox
                st.session_state["nodes"] = st_functions.get_nodes_with_tags_in_bbox(
                    st.session_state.bbox
                )
                # get the tag content as a dictionary
                st.session_state["tags_in_bbox"] = st_functions.count_tag_frequency(
                    st.session_state.nodes
                )

            # show a wordcloud of amenities in the search area
            generate_wordcloud()

            if "tags" in st.session_state:
                st.markdown("Currently shown on map:")
                st.markdown(st.session_state.tags)

            current_selection = st.multiselect(
                "Items to show on map:",
                options=st.session_state.value_frequency.keys(),
                default="bar",
            )

            st.session_state.add_selection = st.checkbox(
                "add_to_map",
            )

            if st.session_state.add_selection:
                # show selected values on the map in different colors
                st.session_state.tags = {
                    st.session_state.selected_key: current_selection
                }
                st.markdown(st.session_state.tags)

                # ToDo: Use this instead of running a new call
                selection = st_functions.filter_nodes_with_tags(
                    st.session_state.nodes, st.session_state.tags
                )

                ## st_folium
                st.session_state.points = st_functions.folium_circles_from_bbox_tags(
                    bbox=st.session_state.bbox,
                    tags=st.session_state.tags,
                )
                # Reset the checkbox
                st.session_state.add_selection = False

        else:
            # If the checkbox is unchecked, clear the session state
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
