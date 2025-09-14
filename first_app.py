import os
import streamlit as st
import geopandas as gpd
import folium

# -----------------------
# Pagina configuratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Dashboard - Test",
    layout="wide"
)

# -----------------------
# Data laden (1x cachen)
# -----------------------
@st.cache_data
def load_geojson(path):
    df = gpd.read_file(path)
    df = df[~df.geometry.isna()].copy()
    df = df.to_crs(epsg=4326)  # altijd in lat/lon voor folium
    return df

monuments_path = os.path.join(
    os.getcwd(),
    "monuments_dashboard_data",
    "municipal_monument_count.geojson"
)
monuments_df = load_geojson(monuments_path)

# -----------------------
# Voorbereiden subset (1x cachen)
# -----------------------
@st.cache_data
def prepare_geo(_df, n=50):
    # Neem sample
    test_df = _df.sample(min(n, len(_df)), random_state=42).copy()
    # Projecteer voor centroid
    test_df_proj = test_df.to_crs(epsg=3857)
    centroid = test_df_proj.geometry.centroid.to_crs(epsg=4326)
    x_center = centroid.x.median()
    y_center = centroid.y.median()
    return test_df, (y_center, x_center)

test_monuments_df, map_center = prepare_geo(monuments_df)

# -----------------------
# Folium kaart maken
# -----------------------
m = folium.Map(
    location=map_center,
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

folium.GeoJson(test_monuments_df).add_to(m)

# -----------------------
# Render kaart (HTML i.p.v. st_folium)
# -----------------------
st.components.v1.html(m._repr_html_(), height=800, scrolling=True)

# Info in sidebar
st.sidebar.markdown(f"**Test met {len(test_monuments_df)} polygonen**")
