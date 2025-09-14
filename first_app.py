import os
import streamlit as st
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
test_monuments_df = monuments_df.sample(min(50, len(monuments_df)), random_state=42).copy()

# -----------------------
# Centroid bepalen voor center van de kaart
# -----------------------
# Projecteer naar een projected CRS om juiste centroid te krijgen
test_monuments_df_proj = test_monuments_df.to_crs(epsg=3857)
centroid_proj = test_monuments_df_proj.geometry.centroid
# Terug naar lat/lon
centroid_latlon = centroid_proj.to_crs(epsg=4326)
x_center_coord = centroid_latlon.x.median()
y_center_coord = centroid_latlon.y.median()

# -----------------------
# Folium kaart maken
# -----------------------
m = folium.Map(
    location=[y_center_coord, x_center_coord],
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

# Voeg GeoJSON toe (zonder styling/tooltip voor eenvoud)
folium.GeoJson(test_monuments_df).add_to(m)

# -----------------------
# Render kaart in Streamlit via HTML
# -----------------------
st.components.v1.html(m._repr_html_(), height=800, scrolling=True)

st.sidebar.markdown(f"**Test met {len(test_monuments_df)} polygonen**")
