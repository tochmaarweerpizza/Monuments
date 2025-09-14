import os
import streamlit as st
import geopandas as gpd
import folium
import numpy as np

# -----------------------
# Pagina configuratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Dashboard - Choropleth Test",
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
    test_df = _df.sample(min(n, len(_df)), random_state=42).copy()
    test_df_proj = test_df.to_crs(epsg=3857)
    centroid = test_df_proj.geometry.centroid.to_crs(epsg=4326)
    x_center = centroid.x.median()
    y_center = centroid.y.median()
    return test_df, (y_center, x_center)

test_monuments_df, map_center = prepare_geo(monuments_df)

# -----------------------
# Sidebar instellingen
# -----------------------
st.sidebar.header("Kleurenschaal instellingen")

col_name = "totaal_monumenten"  # pas aan indien nodig

# Kies methode voor schaalverdeling
scale_type = st.sidebar.selectbox(
    "Kies schaalverdeling",
    ["Kwantielen", "Gelijke intervallen", "Standaard (min-max)"]
)

values = test_monuments_df[col_name].dropna().astype(float)

if scale_type == "Kwantielen":
    thresholds = list(values.quantile([0, 0.2, 0.4, 0.6, 0.8, 1]))
elif scale_type == "Gelijke intervallen":
    thresholds = list(np.linspace(values.min(), values.max(), 6))
else:  # standaard min-max
    thresholds = [values.min(), values.max()/4, values.max()/2, 3*values.max()/4, values.max()]

# Zorg dat waarden uniek zijn en gesorteerd
thresholds = sorted(list(set([round(v, 2) for v in thresholds])))

# -----------------------
# Folium kaart maken
# -----------------------
m = folium.Map(
    location=map_center,
    zoom_start=7.5,
    tiles='CartoDB Positron'
)

folium.Choropleth(
    geo_data=test_monuments_df,
    data=test_monuments_df,
    columns=["id", col_name],   # let op: id moet bestaan
    key_on="feature.properties.id",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    threshold_scale=thresholds,
    legend_name="Aantal monumenten"
).add_to(m)

# -----------------------
# Render kaart
# -----------------------
st.components.v1.html(m._repr_html_(), height=800, scrolling=True)

# Info in sidebar
st.sidebar.markdown(f"**Test met {len(test_monuments_df)} polygonen**")
