import requests
import json
import streamlit as st
import folium
import rasterio
from streamlit_folium import folium_static
import matplotlib.pyplot as plt


def overpass_query(query):
    overpass_url = "http://overpass-api.de/api/interpreter"
    response = requests.get(overpass_url, params={"data": query})
    data = response.json()
    return data


def bbox_from_stfolium_bounds(bounds):
    """
    Return a tuple of coordinates from the "bounds" object returned by streamlit_folium
    bounds = {'_southWest': {'lat': 52.494239118767496, 'lng': 13.329420089721681}, '_northEast': {'lat': 52.50338318818063, 'lng': 13.344976902008058}}
    """
    return (
        bounds["_southWest"]["lat"],
        bounds["_southWest"]["lng"],
        bounds["_northEast"]["lat"],
        bounds["_northEast"]["lng"],
    )


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


def show_tif(filename):
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


def st_folium():
    st.subheader("Streamlit-Folium")
    st.markdown(
        """Using Folium to display the map itself, and streamlit_folium to return \
            some data from interactions with the map. """
    )

    center = {"lat": 52.49881139119491, "lng": 13.33718776702881}

    m = folium.Map(location=list(center.values()), zoom_start=16)
    st_data = st_folium(m, width=725)
    bbox = osm_tools.bbox_from_stfolium_bounds(st_data["bounds"])
    st.text(bbox)

    button_push = st.button(label="Show pharmacies")
    if button_push:
        st.text("running query...")
        data = osm_tools.query_pharmacies_in_bbox(bbox)
        st.text(f"{len(data)} results found")
        ## Add a marker for each node
        for element in data["elements"]:
            st.text(element)
            if "lat" in element and "lon" in element:
                marker = folium.Marker(location=[element["lat"], element["lon"]])
                marker.add_to(m)
    # Show the map after adding the markers
    # st_folium(m, width=725)
