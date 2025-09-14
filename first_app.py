import os
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import numpy as np

# Data laden
@st.cache_data
def load_geojson(path):
    return gpd.read_file(path)

monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))
monuments_df = monuments_df[~monuments_df.geometry.isna()].copy()
monuments_df = monuments_df.to_crs(epsg=4326)

# Kies een numerieke kolom als test
numerical_cols = monuments_df.select_dtypes(include=np.number).columns.tolist()
monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df[numerical_cols[0]]

# Bereken middelpunt via bounds
bounds = monuments_df.total_bounds  # [minx, miny, maxx, maxy]
x_center_coord = (bounds[0] + bounds[2]) / 2
y_center_coord = (bounds[1] + bounds[3]) / 2

# Folium map
m = folium.Map(location=[y_center_coord, x_center_coord], zoom_start=7.5, tiles='CartoDB Positron')

# Schaalverdeling en Choropleth
col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]
scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), len(col_list)+1)

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

# Renderen
st_data = st_folium(m, width=1000, height=800)
