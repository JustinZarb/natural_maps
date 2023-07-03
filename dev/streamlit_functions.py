import requests
import json
import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import utm
from pyproj import CRS, Transformer
import pandas as pd
import plotly.express as px
import osmnx as ox
import folium
import contextily as cx
from shapely.geometry import Polygon, Point, LineString, mapping, MultiPolygon
import pydeck as pdk
from math import sqrt, log
from geopandas import GeoDataFrame
import hashlib


def name_to_gdf(place_name):
    """Return a Pandas.GeoDataframe object for a name if Nominatim can find it

    Args:
        place_name (str): eg. "Berlin"

    Returns:
        gdf: a geodataframe
    """
    # Use OSMnx to geocode the location (OSMnx uses some other libraries)
    gdf = ox.geocode_to_gdf(place_name)
    return gdf


def map_location(gdf=None, feature_group=None, highlight_location=True):
    """Create a map object given an optional gdf and feature group

    Args:
        gdf (_type_, optional): _description_. Defaults to None.
        feature_group (_type_, optional): _description_. Defaults to None.

    Returns:
        map object: _description_
    """
    # Initialize the map
    m = folium.Map(height="50%")

    # Add the gdf to the map
    if highlight_location:
        if gdf is not None:
            folium.GeoJson(gdf).add_to(m)

    # Add the feature group(s) to the map and update the bounds
    if feature_group is not None:
        features = feature_group if isinstance(feature_group, list) else [feature_group]
        for feature in features:
            feature.add_to(m)

    # Fit the map to the bounds of all features
    m.fit_bounds(m.get_bounds())
    return m


def update_map():
    # Create a folium map, adding
    if "gdf" in st.session_state:
        gdf = st.session_state.gdf
    else:
        gdf = None
    if "circles" in st.session_state:
        circles = st.session_state.circles
    else:
        circles = None
    m = map_location(gdf, circles)
    return m


def word_to_color(word):
    # Use MD5 hash to convert the word into a hexadecimal number
    hash_object = hashlib.md5(word.encode())
    hex_dig = hash_object.hexdigest()
    # Take the first 6 characters of the hex number and convert it into an RGB color
    hex_color = hex_dig[:6]
    r = int(hex_color[:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    a = 255
    # Return the RGB color as a tuple
    return f"rgb({r}, {g}, {b})"


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


def gdf_data_old(gdf):
    """Get the area of a polygon
    can take a gdf with multiple rows"""
    places_dict = {}
    for index, row in gdf.iterrows():
        print(index)
        utm_zone = utm.latlon_to_zone_number(
            gdf.loc[[index], "lat"].values[0], gdf.loc[[index], "lon"].values[0]
        )
        south = gdf.loc[[index], "lat"].values[0] < 0
        crs = CRS.from_dict({"proj": "utm", "zone": utm_zone, "south": south})
        epsg_code = crs.to_authority()[1]
        unit = list({ai.unit_name for ai in crs.axis_info})[0]
        gdf_projected = gdf.loc[[index], :].to_crs(epsg_code)
        area = gdf_projected.area.values[0]
        places_dict[row["display_name"]] = {
            "area": area,
            "unit": unit,
        }
    return places_dict


def gdf_data(row, original_crs):
    """Get the area of a polygon
    can take a row of a gdf"""
    utm_zone = utm.latlon_to_zone_number(row["lat"], row["lon"])
    south = row["lat"] < 0
    utm_crs = CRS.from_dict({"proj": "utm", "zone": utm_zone, "south": south})
    epsg_code = utm_crs.to_authority()[1]
    unit = list({ai.unit_name for ai in utm_crs.axis_info})[0]
    gdf_projected = GeoDataFrame([row], crs=original_crs).to_crs(epsg_code)
    area = gdf_projected.area.values[0]
    return pd.Series({"area": area, "unit": f"square {unit}"})


def longest_distance_to_vertex(geometry):
    """Calculate the radius between the polygon centroid and its furthest point.
    Not callable by the LLM
    Args:
        polygon (shapely.geometry.Polygon): _description_
    Returns:
        max_distance (float): _description_
    """
    # Check if the geometry is a MultiPolygon
    if isinstance(geometry, MultiPolygon):
        # If it is, iterate over the individual polygons
        polygons = list(geometry)
    else:
        # If it's not a MultiPolygon, assume it's a single Polygon and put it in a list
        polygons = [geometry]

    max_distance = 0
    for polygon in polygons:
        centroid = polygon.centroid
        # Calculate the distance from the centroid to each vertex
        distances = [
            centroid.distance(Point(vertex)) for vertex in polygon.exterior.coords
        ]
        # Update max_distance if the maximum distance for this polygon is greater
        max_distance = max(max_distance, max(distances))

    # Return the maximum distance
    return max_distance


def count_tag_frequency(datasets, tag=None):
    tag_frequency = {}

    # Combine elements of all datasets into a single list
    elements = [element for data in datasets for element in data["elements"]]

    for element in elements:
        if "tags" in element:
            for t, v in element["tags"].items():
                # Split the tag on the first separator
                t = t.split(":")[0]

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

    # Sort the dictionary by its values in descending order
    tag_frequency = {
        k: v
        for k, v in sorted(
            tag_frequency.items(), key=lambda item: item[1], reverse=True
        )
    }

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


def get_nodes_with_tags_in_bbox(bbox: list):
    """Get unique tag keys within a bounding box and plot the top 200 in a wordcloud
    In this case it is necessary to run a query in overpass because
    osmnx.geometries.geometries_from_bbox requires an input for "tags", but here
    we want to get all of them.

    ToDo: Limit the query size

    returns:
        data: the query response in json format
    """
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


def get_points_from_bbox_and_tags(bbox: list, tags: dict):
    """Run a Overpass query given bbox and tags"""
    # bbox = [S, W, N, E]
    west = bbox[1]
    south = bbox[0]
    north = bbox[2]
    east = bbox[3]

    poly_from_bbox = Polygon(
        [(west, south), (east, south), (east, north), (west, north)]
    )

    geometries = ox.geometries_from_polygon(poly_from_bbox, tags)
    return geometries


def filter_nodes_with_tags(nodes: dict, tags: dict):
    """Get a subset of nodes from some geometry returned by overpass

    Args:
        nodes (dict): Objects returned from Overpass
        tags (dict): Tags to search for
    """
    selection = {}

    for key, values in tags.items():
        for value in values:
            selection[value] = [
                e
                for e in nodes["elements"]
                if (key in e["tags"].keys()) and (value in e["tags"].values())
            ]

    return selection


def create_circles_from_nodes(json_obj):
    # Loop over each node in the 'bar' key of the JSON object
    circles = []
    for tag_key in json_obj.keys():
        color = word_to_color(tag_key)
        for node in json_obj[tag_key]:
            # Get the latitude and longitude of the node
            lat = node["lat"]
            lon = node["lon"]

            # Get the 'tags' dictionary
            tags = node["tags"]

            # Create a string for the hover text
            hover_text = (
                f"{tag_key}: {tags.get('name', 'N/A')}\n"  # Add more details here
            )

            # Create a circle on the map for this key
            circles.append(
                folium.Circle(
                    location=[lat, lon],
                    radius=5,  # Set the radius as needed
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.4,
                    tooltip=hover_text,
                )
            )

    return circles
