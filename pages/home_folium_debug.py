import streamlit as st
import dev.streamlit_functions as st_functions
import streamlit_folium as st_folium

# Text input for place name
place_name = st.text_input(
    "Location",
    value="Augsburger Strasse, Berlin",
)

st.session_state.place_name = place_name
st.session_state.gdf = st_functions.name_to_gdf(place_name)


# Function to update map
def update_map(gdf, feature_group=None):
    m = st_functions.map_location(gdf, feature_group)
    return m


# Columns
left, right = st.columns((1, 2), gap="small")

with left:
    # Create a placeholder for the map
    st.session_state.map_placeholder = st.empty()

    # Create the map and st_data if not in session_state
    if "map" not in st.session_state:
        st.session_state.map = update_map(st.session_state.gdf)
        st.session_state.st_data = st.session_state.map_placeholder.st_folium(
            st.session_state.map, width=600, height=600
        )
    else:
        # Update the st_data with the current map
        st.session_state.st_data = st.session_state.map_placeholder.st_folium(
            st.session_state.map, width=600, height=600
        )

with right:
    # Check the zoom level from st_data
    if st.session_state.st_data is not None and st.session_state.st_data["zoom"] >= 13:
        st.session_state.explore_view = st.checkbox(
            label="Common tags in this view", value=False, key="explore_view"
        )

        # If the checkbox is checked, walk the user through some steps to get points of interest
        if st.session_state.explore_view:
            st.subheader("Tags in this area")

            # Assuming get_points_of_interest returns points, this is an example (you'll need to define this function)
            # points = get_points_of_interest(st.session_state.map)

            # Update map with points (assuming points is defined)
            # st.session_state.map = update_map(st.session_state.gdf, points)
            # st.session_state.st_data = st.session_state.map_placeholder.st_folium(st.session_state.map, width=600, height=600)
    else:
        st.markdown("Zoom in to see what's in the map")
