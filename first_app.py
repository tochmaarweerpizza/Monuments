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
st.set_page_config(page_title="Minimal Polygonenkaart", layout="wide")

# -----------------------
# Data laden
# -----------------------
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))
monuments_df = monuments_df[~monuments_df.geometry.isna()]

# Dummy kolom voor kleurklasse (als je echte kolom wilt gebruiken, vervang dit)
monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df['Aantal'] if 'Aantal' in monuments_df.columns else np.random.randint(0, 500, len(monuments_df))

# -----------------------
# Bepaal schaal en kleuren
# -----------------------
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]

# 5 bins op basis van max waarde
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), 6)
scale = np.round(scale, 1)

# -----------------------
# Folium kaart
# -----------------------
x_center_coord = np.median(monuments_df.centroid.to_crs('epsg:4326').x)
y_center_coord = np.mean(monuments_df.centroid.to_crs('epsg:4326').y)
m = folium.Map(location=[y_center_coord, x_center_coord], zoom_start=7.5, tiles='CartoDB Positron')

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

# Dynamische legenda
legend_html = """
<div style="position: fixed; 
            bottom: 50px; left: 50px; width: 200px; height: 150px; 
            background-color: white; z-index:9999; font-size:14px;
            border:2px solid grey; padding: 10px;">
    <b>Aantal monumenten</b><br>
"""
for i in range(len(col_list)):
    legend_html += f'<i style="background:{col_list[i]};width:18px;height:18px;float:left;margin-right:8px;"></i>({scale[i]}, {scale[i+1]}]<br>'
legend_html += "</div>"

m.get_root().html.add_child(folium.Element(legend_html))

# -----------------------
# Render kaart
# -----------------------
st_folium(m, width=1000, height=800)
