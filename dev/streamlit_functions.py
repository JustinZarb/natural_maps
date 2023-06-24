import requests
import json
import streamlit as st
import folium
import rasterio
from streamlit_folium import st_folium, folium_static
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

import pandas as pd
import plotly.express as px
import osmnx as ox
import folium
import contextily as cx


def overpass_query(query):
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url, params={"data": query})
    data = response.json()
    return data


def bbox_from_st_data(bounds):
    """
    Return a tuple of coordinates from the "bounds" object returned by streamlit_folium
    bounds = {'_southWest': {'lat': 52.494239118767496, 'lng': 13.329420089721681}, '_northEast': {'lat': 52.50338318818063, 'lng': 13.344976902008058}}
    """
    bbox = [
        bounds["_southWest"]["lat"],
        bounds["_southWest"]["lng"],
        bounds["_northEast"]["lat"],
        bounds["_northEast"]["lng"],
    ]
    return bbox


def map_location(place_name):
    # Use OSMnx to geocode the location
    gdf = ox.geocode_to_gdf(place_name)

    # Get the geometry type of the location
    geometry_type = gdf["geometry"].iloc[0].geom_type

    # If the geometry is a point, create a map centered around the point
    if geometry_type == "Point":
        m = folium.Map(
            location=[gdf["geometry"].iloc[0].y, gdf["geometry"].iloc[0].x],
            zoom_start=14,
            width=100,
        )

    # If the geometry is not a point, create a map of the region
    else:
        minx, miny, maxx, maxy = gdf["geometry"].iloc[0].bounds
        m = folium.Map(location=[(miny + maxy) / 2, (minx + maxx) / 2], width="100")
        m.fit_bounds([[miny, minx], [maxy, maxx]])
        folium.GeoJson(gdf).add_to(m)

    st_data = st_folium(m)

    return st_data


def count_tag_frequency(data, tag=None):
    tag_frequency = {}

    for element in data["elements"]:
        if "tags" in element:
            for t, v in element["tags"].items():
                if tag is None:
                    # Counting tag frequency
                    if t in tag_frequency:
                        tag_frequency[t] += 1
                    else:
                        tag_frequency[t] = 1
                else:
                    # Counting value frequency for a specific tag
                    if t == tag:
                        if v in tag_frequency:
                            tag_frequency[v] += 1
                        else:
                            tag_frequency[v] = 1

    return tag_frequency


def generate_wordcloud(frequency_dict):
    tags_freq = [(tag, freq) for tag, freq in frequency_dict.items()]
    tags_freq.sort(key=lambda x: x[1], reverse=True)  # Sort tags by frequency
    tags_freq_200 = tags_freq[:200]  # Limit to top 200 tags

    wordcloud = WordCloud(
        width=800,
        height=200,
        background_color="white",
        stopwords=STOPWORDS,
        colormap="viridis",
        random_state=42,
    )
    wordcloud.generate_from_frequencies({tag: freq for tag, freq in tags_freq_200})
    return wordcloud


def get_unique_tags_in_bbox(bbox: list):
    """Get unique tag keys within a bounding box and plot the top 200 in a wordcloud
    returns:
        data: the query response in json format
    """
    # Run overpass query for the given bounding box
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node({bbox[0]}, {bbox[1]}, {bbox[2]}, {bbox[3]})[~"."~"."];
    );
    out body;
    """
    response = requests.get(overpass_url, params={"data": overpass_query})
    data = response.json()

    return data


def get_tag_keys():
    # Seems excessive
    url = "https://taginfo.openstreetmap.org/api/4/keys/all"
    response = requests.get(url)
    data = response.json()
    return data["data"]


def get_tags(place_name, tags_keys):
    objects = ox.geometries.geometries_from_place(place_name, tags_keys)
    return objects


def plot_network(place_name):
    G = ox.graph_from_place(place_name, network_type="drive")
    fig, ax = ox.plot_graph(ox.project_graph(G), show=False, close=False)
    st.pyplot(fig)


def simple_folium_map():
    st.markdown(
        """Using Folium to display the map itself, and streamlit_folium to return \
            some data from interactions with the map. """
    )

    center = {"lat": 52.49881139119491, "lng": 13.33718776702881}
    button_push = st.button(label="Show pharmacies")

    if button_push:
        st.text("running query...")
        data = query_pharmacies_in_bbox(bbox)
        st.text(f"{len(data)} results found")
        ## Add a marker for each node
        for element in data["elements"]:
            st.text(element)
            if "lat" in element and "lon" in element:
                marker = folium.Marker(location=[element["lat"], element["lon"]])
                marker.add_to(m)

    m = folium.Map(location=list(center.values()), zoom_start=16)
    st_data = st_folium(m, width=725)
    bbox = bbox_from_stfolium_bounds(st_data["bounds"])
    st.text(bbox)

    # Show the map after adding the markers
    # st_folium(m, width=725)


#### Older functions


def query_pharmacies_in_bbox(bbox):
    # Overpass query
    query = f"""
    [out:json];
    node[amenity=pharmacy]{bbox};
    out;
    """
    return overpass_query(query)


def query_outdoor_seating_in_bbox(bbox):
    query = f"""[out:json][timeout:25];
      // gather results
      (
        // query part for: “outdoor_seating=yes”
        node["outdoor_seating"="yes"]({bbox});
        way["outdoor_seating"="yes"]({bbox});
        relation["outdoor_seating"="yes"]({bbox});
      );
      // print results
      out body;
      >;
      out skel qt;"""
    return overpass_query(query)


def map_with_geotiff(filename):
    # Open the GeoTIFF file with rasterio
    with rasterio.open(filename) as ds:
        # Get the GeoTIFF's bounds and transform
        data = ds.read(1)
        bounds = ds.bounds
        transform = ds.transform
        plt.imsave("hillshade.png", data, cmap="gray")
    # Calculate the center of the map
    center = ((bounds.top + bounds.bottom) / 2, (bounds.left + bounds.right) / 2)

    # Create a new folium map centered on the GeoTIFF
    m = folium.Map(location=center, zoom_start=16)

    # Add the GeoTIFF as a TileLayer (requires a local server or publicly accessible URL)
    folium.raster_layers.ImageOverlay(
        image="hillshade.png",
        bounds=[[bounds.bottom, bounds.left], [bounds.top, bounds.right]],
        opacity=0.4,
    ).add_to(m)

    # Show the map in the Streamlit app
    folium_static(m)
