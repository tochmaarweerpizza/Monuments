import os
import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# -----------------------
# Paginaconfiguratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Data laden
# -----------------------
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

# -----------------------
# GeoDataFrame met monumentaantallen
# -----------------------
monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))
column_mapping_df = load_csv(os.path.join(os.getcwd(), "monuments_dashboard_data", "monument_category_column_mapping.csv"))

# verwijder rijen zonder geometrie
monuments_df = monuments_df[~monuments_df.geometry.isna()].copy()

# -----------------------
# Bereken aantal_monumenten_binnen_categorie
# -----------------------
selected_columns = column_mapping_df['column_mapping']
monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df[selected_columns].sum(axis=1)

# -----------------------
# Centrum voor kaart
# -----------------------
# Eerst naar CRS EPSG:3857 projecteren voor correcte centroiden
monuments_df = monuments_df.to_crs(epsg=3857)
x_center_coord = float(monuments_df.geometry.centroid.x.median())
y_center_coord = float(monuments_df.geometry.centroid.y.median())

# Zet weer naar WGS84 voor folium
monuments_df = monuments_df.to_crs(epsg=4326)

# -----------------------
# Folium kaart
# -----------------------
m = folium.Map(
    location=[y_center_coord, x_center_coord],
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

# Kleurindeling
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), 5).tolist()
scale = np.round(scale, 1)

def style_function(feature):
    area = feature['properties'].get('aantal_monumenten_binnen_categorie', 0)
    if area <= scale[1]:
        color = col_list[0]
    elif area <= scale[2]:
        color = col_list[1]
    elif area <= scale[3]:
        color = col_list[2]
    elif area <= scale[4]:
        color = col_list[3]
    else:
        color = col_list[4]
    return {'fillOpacity': 1, 'weight': 1, 'color': 'black', 'fillColor': color}

folium.GeoJson(monuments_df, style_function=style_function).add_to(m)

# -----------------------
# Render kaart in Streamlit
# -----------------------
st_data = st_folium(m, width=1000, height=800)
