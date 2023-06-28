import plotly.express as px
import geopandas as gpd
import shapely.geometry
import numpy as np
import streamlit as st
import wget
import pandas as pd

us_cities = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/us-cities-top-1k.csv"
)
us_cities = us_cities.query("State in ['New York', 'Ohio']")
fig = px.line_mapbox(us_cities, lat="lat", lon="lon", color="State", zoom=3, height=300)

fig.update_layout(
    mapbox_style="stamen-terrain",
    mapbox_zoom=4,
    mapbox_center_lat=41,
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
)


st.header("left")
st.plotly_chart(fig)
st.markdown(fig.to_plotly_json())
