import streamlit as st
import dev.streamlit_functions as st_functions
import folium
from streamlit_folium import st_folium
import pydeck as pdk

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

st.session_state.place_name = place_name
st.session_state.gdf = st_functions.name_to_gdf(place_name)

st.session_state.feature_group = st.empty()


def update_map(gdf, feature_group=None):
    m = st_functions.map_location(gdf, feature_group)
    # Display the updated map in the placeholder
    with st.session_state.st_data:
        st_folium(m)


# Columns
left, right = st.columns((1, 2), gap="small")
with left:
    ## First map: Folium
    # Create the map
    st.session_state.st_data = st.empty()
    st_data = update_map(st.session_state.gdf)

with right:
    if st_data is not None and st_data["zoom"] >= 13:
        st.checkbox(label=f"Common tags in this view", value=False, key="explore_view")
        # Create a checkbox that will control whether the map and data are stored in the session state
        if st.session_state.explore_view:
            # check if  m and st_data already exist in the session state
            if st_data in st.session_state:
                pass
            else:
                # If the checkbox is checked, store the map and data in the session state
                # st.session_state["m"] = m
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
            # show selected values on the map in different colors
            if st.session_state.selected_values is not None:
                tags = {st.session_state.selected_key: st.session_state.selected_values}
                st.markdown(tags)
                selection = st_functions.filter_nodes_with_tags(
                    st.session_state.nodes, tags
                )

                ## st_folium
                points = st_functions.folium_circles_from_bbox_tags(
                    bbox=st.session_state.bbox,
                    tags=tags,
                )
                st.markdown(points)

                # update_map(st.session_state.gdf, points)

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
