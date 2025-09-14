import os
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np

st.set_page_config(page_title="Minimal Polygonenkaart", layout="wide")

# Data laden
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))

# Alleen rijen met geometrie
monuments_df = monuments_df[~monuments_df.geometry.isna()]

# Zet CRS naar EPSG:4326
monuments_df = monuments_df.to_crs(epsg=4326)

# Dummy kolom voor kleurklasse
monuments_df['aantal_monumenten_binnen_categorie'] = np.random.randint(0, 500, len(monuments_df))

# Bepaal centrum
x_center_coord = float(monuments_df.geometry.centroid.x.median())
y_center_coord = float(monuments_df.geometry.centroid.y.median())

# Maak kaart
m = folium.Map(location=[y_center_coord, x_center_coord], zoom_start=7.5, tiles='CartoDB Positron')

# Schaal en kleuren
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), 6)
scale = np.round(scale, 1)

def style_function(feature):
    value = feature['properties'].get('aantal_monumenten_binnen_categorie', 0)
    if value <= scale[1]:
        color = col_list[0]
    elif value <= scale[2]:
        color = col_list[1]
    elif value <= scale[3]:
        color = col_list[2]
    elif value <= scale[4]:
        color = col_list[3]
    else:
        color = col_list[4]
    return {'fillOpacity': 1, 'weight': 1, 'color': 'black', 'fillColor': color}

folium.GeoJson(monuments_df, style_function=style_function).add_to(m)

st_folium(m, width=1000, height=800)
