import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import numpy as np

# -----------------------
# Pagina configuratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Dashboard - Test",
    layout="wide"
)

# -----------------------
# Data laden
# -----------------------
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

monuments_path = os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson")
monuments_df = load_geojson(monuments_path)

# -----------------------
# Subset voor testen
# -----------------------
# Neem een kleine sample (bv. 50 polygonen) voor cloud test
test_monuments_df = monuments_df.sample(min(50, len(monuments_df)), random_state=42).copy()

# -----------------------
# Centroid bepalen voor center van de kaart
# -----------------------
# Converteer eerst naar een projected CRS om waarschuwingen te vermijden
test_monuments_df_proj = test_monuments_df.to_crs(epsg=3857)  # Web Mercator
x_center_coord = test_monuments_df_proj.geometry.centroid.x.median()
y_center_coord = test_monuments_df_proj.geometry.centroid.y.median()
# Terug naar lat/lon
import pyproj
from shapely.ops import transform
project = pyproj.Transformer.from_crs("epsg:3857", "epsg:4326", always_xy=True).transform
center_lon, center_lat = transform(project, type('dummy', (object,), {'x': x_center_coord, 'y': y_center_coord})())

# -----------------------
# Folium kaart maken
# -----------------------
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

# Voeg GeoJSON toe (zonder styling/tooltip voor eenvoud)
folium.GeoJson(test_monuments_df).add_to(m)

# -----------------------
# Render kaart in Streamlit via HTML (om st_folium probleem te vermijden)
# -----------------------
st.components.v1.html(m._repr_html_(), height=800, scrolling=True)

st.sidebar.markdown(f"**Test met {len(test_monuments_df)} polygonen**")
