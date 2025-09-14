import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np

# -----------------------
# Pagina-configuratie
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

monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))

# Zorg dat geometrie geldig is en CRS correct
monuments_df = monuments_df[~monuments_df.geometry.isna()].copy()
monuments_df = monuments_df.to_crs(epsg=4326)

# Voeg kolom "aantal_monumenten_binnen_categorie" toe als voorbeeld
# Hier kun je aanpassen aan je selectie
monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df['totaal_monumenten']

# -----------------------
# Bepaal middelpunt en zoom
# -----------------------
x_center_coord = monuments_df.geometry.centroid.x.median()
y_center_coord = monuments_df.geometry.centroid.y.median()
zoomstart = 7.5

# -----------------------
# Folium kaart
# -----------------------
m = folium.Map(
    location=[y_center_coord, x_center_coord],
    zoom_start=zoomstart,
    tiles='CartoDB Positron'
)

# Kleurenschaal
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]

# Maak schaalverdeling (gelijke intervallen)
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), len(col_list)+1)

# Choropleth toevoegen
folium.Choropleth(
    geo_data=monuments_df,
    data=monuments_df,
    columns=['naam', 'aantal_monumenten_binnen_categorie'],
    key_on='feature.properties.naam',
    fill_color='YlOrRd',
    fill_opacity=0.8,
    line_opacity=0.5,
    bins=scale.tolist(),
    legend_name='Aantal monumenten'
).add_to(m)

# -----------------------
# Kaart renderen
# -----------------------
st_data = st_folium(m, width=1000, height=800)
