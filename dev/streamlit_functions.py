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
from shapely.geometry import Polygon, Point, LineString, mapping
import pydeck as pdk
from math import sqrt, log
from pyproj import Transformer
import hashlib


def overpass_to_feature_group(data_str=""):
    """Takes the  result of an overpass query in string form as input.
    Selects 'elements' as nodes. Creates a folium.FeatureGroup.
    Adds a Marker for each node,  with coordinates and a tags dictionary."""

    # need to convert the string into a dictionary first.
    data = folium.GeoJson(data_str).data
    # these are the nodes we want
    nodes = data["elements"]
    node_data = [(node["lat"], node["lon"], node["tags"]) for node in nodes]
    fg = folium.FeatureGroup(name="Elements from overpass")
    # the tags content needs to be reformatted
    for lat, lon, tags in node_data:
        tags_content = "<br>".join([f"<b>{k}</b>: {v}" for k, v in tags.items()])
        fg.add_child(folium.Marker(location=[lat, lon], popup=tags_content))
    return fg


def calculate_center(bounds):
    center = ((bounds[0][0] + bounds[1][0]) / 2, (bounds[0][1] + bounds[1][1]) / 2)
    return center


def calculate_zoom_level(bounds):
    """Calculate zoom level for PYDECK

    Args:
        gdf (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Get the bounds of the geometry
    minx, miny, maxx, maxy = bounds[0][0], bounds[0][1], bounds[1][0], bounds[1][1]

    # Calculate the diagonal length of the bounding box
    diagonal_length = sqrt((maxx - minx) ** 2 + (maxy - miny) ** 2)

    # Calculate a base zoom level based on the diagonal length
    # This is a rough estimate and may need to be adjusted to fit your specific needs
    base_zoom = 9 - log(maxx - minx + 0.001)

    # Make sure the zoom level is within the valid range (0-22)
    zoom_level = max(0, min(base_zoom, 22))

    return zoom_level


def calculate_parameters_for_map(overpass_answer):
    """
    takes an overpass answer string
    and returns:
    fg, center, zoom
    """
    fg = overpass_to_feature_group(overpass_answer)
    # Nasty hack for empty answers
    bounds = fg.get_bounds()
    if bounds == [[None, None], [None, None]]:
        bounds = [[52.5210821, 13.3942864], [52.525776, 13.4038867]]
    center = calculate_center(bounds)
    zoom = calculate_zoom_level(bounds)
    return fg, center, zoom


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


def map_location(gdf=None, feature_group=None):
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


# def bounds_to_st_data(gdf):
#     """
#     Return a tuple of coordinates for the "bounds" needed by streamlit_folium
#     """

#     bounds = {'_southWest': {'lat': gdf.bbox_west.values[0], 'lng': gdf.bbox_south.values[0], '_northEast': {'lat': 52.50338318818063, 'lng': 13.344976902008058}}
#     return bounds


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


def gdf_to_layer(gdf):
    """Create layer to visualize in PYDECK

    Args:
        gdf (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Get the geometry type of the location
    geometry_type = gdf["geometry"].iloc[0].geom_type
    # Convert the GeoDataFrame to a DataFrame
    df = gdf.drop(columns=["geometry"])

    if geometry_type == "Point":
        df["lat"] = gdf["geometry"].y
        df["lon"] = gdf["geometry"].x
        # Create a scatterplot layer
        layer = pdk.Layer(
            "ScatterplotLayer",
            df,
            get_position=["lon", "lat"],
            get_radius=100,
            get_fill_color=[255, 0, 0],
        )
    else:
        df["geometry"] = gdf["geometry"].apply(
            lambda geom: mapping(geom)["coordinates"]
        )
        # Create a GeoJsonLayer
        layer = pdk.Layer(
            "PolygonLayer",
            df,
            get_polygon="geometry",
            get_fill_color=[255, 0, 0, 20],  # Set a static color
            get_line_color=[255, 0, 0],
            get_line_width="zoom_level",
            stroked=True,
            # filled=True,
            extruded=False,
        )

    return layer


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


def get_tags(place_name, tags_keys):
    objects = ox.geometries.geometries_from_place(place_name, tags_keys)
    return objects


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


#### Older functions


def pydeck_scatter_from_points(chart_data):
    """Generate a scatterplot layer from a list of points

    Args:
        geometries (_type_): _description_
    """

    scatterplot_layer = pdk.Layer(
        "ScatterplotLayer",
        data=chart_data,
        get_position="[lon, lat]",
        get_color="[200, 30, 0, 160]",
        get_radius=200,
    )
    return


def plot_network(place_name):
    G = ox.graph_from_place(place_name, network_type="drive")
    fig, ax = ox.plot_graph(ox.project_graph(G), show=False, close=False)
    st.pyplot(fig)


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


def folium_circles_from_bbox_tags(bbox: list, tags: dict):
    """Create folium circle markers for nodes on map.

    Args:
        m (folium.map): st.folium map to modify
        bbox (list): bounding box returned by streamlit folium
        tags (dict): a dictionary of tags to add to the map

    Returns:

    """
    geometries = get_points_from_bbox_and_tags(bbox, tags)

    points = []
    # Add geometries to m
    for _, row in geometries.iterrows():
        for tag in tags:
            if tag in row and row[tag]:
                # If the geometry is a point, add a CircleMarker
                if isinstance(row["geometry"], Point):
                    x, y = list(row["geometry"].coords)[0]
                    points.append(
                        folium.CircleMarker(
                            location=[y, x],
                            radius=5,
                            fill=True,
                            fill_color="red",
                            fill_opacity=1.0,
                            popup=tag,
                        )
                    )

    return points


def map_location_pydeck(gdf, layers=[]):
    # Get the geometry type of the location
    geometry_type = gdf["geometry"].iloc[0].geom_type

    # If the geometry is a point, create a map centered around the point
    if geometry_type == "Point":
        center_lat = gdf["geometry"].iloc[0].y
        center_lon = gdf["geometry"].iloc[0].x
        zoom_level = 14

    # If the geometry is not a point, calculate the center and zoom level
    else:
        minx, miny, maxx, maxy = gdf["geometry"].iloc[0].bounds
        center_lat = (miny + maxy) / 2
        center_lon = (minx + maxx) / 2

        # Make sure the zoom level is within the valid range (0-22)
        zoom_level = calculate_zoom_level(gdf)

    # Create the initial view state
    view_state = pdk.ViewState(
        latitude=center_lat, longitude=center_lon, zoom=zoom_level, pitch=0, bearing=0
    )

    # Create layer from gdf
    location_layer = gdf_to_layer(gdf)
    layers.append(location_layer)

    # Create the deck
    deck = pdk.Deck(
        map_style="mapbox://styles/mapbox/outdoors-v11",
        layers=layers,  # Add your layers here
        initial_view_state=view_state,
    )

    return deck
