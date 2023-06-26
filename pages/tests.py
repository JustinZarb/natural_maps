import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

chart_data = pd.DataFrame(
    np.random.randn(1000, 2) / [50, 50] + [37.76, -122.4], columns=["lat", "lon"]
)

# Create an initial map
initial_map = pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=37.76,
        longitude=-122.4,
        zoom=11,
        pitch=50,
    ),
    layers=[],
)

map_placeholder = st.empty()
map_placeholder.pydeck_chart(initial_map)

# Wait for user input to add the layers
if st.button("Add layers"):
    # Create the layers
    hexagon_layer = pdk.Layer(
        "HexagonLayer",
        data=chart_data,
        get_position="[lon, lat]",
        radius=200,
        elevation_scale=4,
        elevation_range=[0, 1000],
        pickable=True,
        extruded=True,
    )
    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=chart_data,
        get_position="[lon, lat]",
        get_color="[200, 30, 0, 160]",
        get_radius=200,
    )

    # Add the layers to the map
    map = pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=37.76,
            longitude=-122.4,
            zoom=11,
            pitch=50,
        ),
        layers=[hexagon_layer, scatterplot_layer],
    )

    # Update the map in the placeholder
    map_placeholder.pydeck_chart(map)
