import streamlit as st
import os
import folium

import dev.osm_tools as osm_tools

st.set_page_config(
    page_title="Naturalmaps",
    page_icon=":world_map:️",
    layout="wide",
)

st.title("Natural Maps")
st.markdown(
    "A Portfolio project by J. Adam Hughes, Pasquale Zito and Justin Zarb as part of Data Science Retreat. [Github Repo](https://github.com/JustinZarb/shade-calculator)"
)

left, right = st.columns(2)

with left:
    st.header("Natural language input")
    natural_input = st.text_area(
        "What would you like to know?",
    )
    b = st.button("Translate to Overpass Query")
    st.header("Generated query")
    st.markdown(
        """
        - #Todo: Test a zero-shot with a pretrained LLM
        - #Todo: Finetune
        """
    )
    st.info(
        """
        #### Example query
        [out:json][timeout:25];
        // gather results
        (
        // query part for: “outdoor_seating=yes”
        node["outdoor_seating"="yes"]({{bbox}});
        way["outdoor_seating"="yes"]({{bbox}});
        relation["outdoor_seating"="yes"]({{bbox}});
        );
        // print results
        out body;
        >;
        out skel qt;
        """
    )
    st.markdown(
        """
        This is where we will use NLP to create Overpass or postGIS queries from the prompt given above.
        The goal is to create a better version of [Overpass Turbo](https://wiki.openstreetmap.org/wiki/Overpass_turbo/Wizard), which we found not to be very intuitive.
        """
    )

    st.header("Process query results")
    st.markdown("""Do something with the results""")


with right:
    st.header("Map display")
    tif_path = os.path.join(
        os.path.join(os.path.join(os.path.join(".", "dev"), "shadowcalc"), "data"),
        "hillshade.tif",
    )
    st.markdown("*Show map with markers*")
    osm_tools.simple_folium_map()

st.header("How to use this tool")
st.markdown(
    """Open Street Map is awesome but hard to query. We are here to study what can
     be done and streamline the process of question -> query -> process -> output. 
     Here are some examples of how we imagine this to be used: 
     """
)
st.markdown(
    """
| Persona         | Description | Spatial Query |
|-----------------|-------------|---------------|
| Urban Athlete   | Enjoys staying active and exploring the city in a dynamic way. | Find all the parks in Berlin that have a running path of at least 5km and are within 500m of a public swimming pool for a post-run dip. |
| Hungry Partygoer | Enjoys the vibrant nightlife of the city and loves to eat late-night snacks. | Find all the late-night food spots that are within a 200m radius of nightclubs that are open until at least 3 AM. |
| City Planner | Interested in understanding and improving the urban layout of the city. | Find all residential buildings in Berlin that are more than 50m high and are not within 500m of any public park or green space. |
| Culture Seeker | Always looking to explore cultural heritage and history. | Find all the historic landmarks in Berlin that are within a 1km radius of an art gallery or museum. |
| Freelance Writer | Always in search of quiet spots to sit, observe, and pen their thoughts. | Find all the quietest coffee shops (at least 200m away from any main road) in Berlin that open before 8 AM and are in close proximity to a library or a bookstore. |

"""
)
