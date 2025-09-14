import os
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np

# -----------------------
# Paginaconfiguratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Polygonenkaart",
    layout="wide"
)

# -----------------------
# GeoJSON laden
# -----------------------
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

geojson_path = os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson")
monuments_df = load_geojson(geojson_path)

# Verwijder geometrieën zonder data
monuments_df = monuments_df[~monuments_df.geometry.isna()].copy()

# -----------------------
# Centrum van kaart
# -----------------------
# Let op CRS: eerst naar EPSG:3857 projecteren voor centroid
monuments_proj = monuments_df.to_crs(epsg=3857)
x_center_coord = float(monuments_proj.geometry.centroid.x.median())
y_center_coord = float(monuments_proj.geometry.centroid.y.median())

# Terug naar WGS84 voor Folium
center_geom = gpd.GeoSeries(gpd.points_from_xy([x_center_coord], [y_center_coord]), crs=3857).to_crs(epsg=4326)
x_center_coord = float(center_geom.x)
y_center_coord = float(center_geom.y)

# -----------------------
# Kleur per polygon
# -----------------------
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), 6)
scale = np.round(scale, 1)

def get_color(value):
    if value <= scale[1]:
        return col_list[0]
    elif value <= scale[2]:
        return col_list[1]
    elif value <= scale[3]:
        return col_list[2]
    elif value <= scale[4]:
        return col_list[3]
    else:
        return col_list[4]

monuments_df['color'] = monuments_df['aantal_monumenten_binnen_categorie'].apply(get_color)

# -----------------------
# Folium kaart
# -----------------------
m = folium.Map(
    location=[y_center_coord, x_center_coord],
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

folium.GeoJson(
    monuments_df,
    style=lambda feature: {
        'fillColor': feature['properties']['color'],
        'color': 'black',
        'weight': 1,
        'fillOpacity': 1
    }
).add_to(m)

# -----------------------
# Render kaart in Streamlit
# -----------------------
st_folium(m, width=1000, height=800)
