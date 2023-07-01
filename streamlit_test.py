import streamlit as st
import dev.streamlit_functions as st_functions
from dev.st_explore_with_wordcloud import explore_data
import folium
from streamlit_folium import st_folium
import pydeck as pdk

import os
import json
import pandas as pd
import requests
from time import gmtime, strftime
from streamlit_folium import st_folium

m = folium.Map()
m.save("footprint.html")

# center on Liberty Bell, add marker
m = folium.Map(location=[39.949610, -75.150282], zoom_start=16)
folium.Marker(
    [39.949610, -75.150282], popup="Liberty Bell", tooltip="Liberty Bell"
).add_to(m)

from folium.plugins import Draw

Draw(export=True).add_to(m)

c1, c2 = st.columns(2)
with c1:
    output = st_folium(m, width=700, height=500)

with c2:
    st.write(output)

# call to render Folium map in Streamlit
# st_data = st_folium(m, width=725)

m2 = folium.Map(location=[-33.8587, 151.2140], zoom_start=16)
tooltip = "Liberty Bell"
folium.Marker([39.949610, -75.150282], popup="Liberty Bell", tooltip=tooltip).add_to(m)

# call to render Folium map in Streamlit
st_folium(m2, width=2000, height=500, returned_objects=[])
