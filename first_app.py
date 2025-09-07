import os
import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
import folium
from folium import FeatureGroup
from streamlit_folium import st_folium
from branca.element import Template, MacroElement

# -----------------------
# Paginaconfiguratie
# -----------------------
st.set_page_config(
    page_title="Rijksmonumenten Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------
# Titel in sidebar
# -----------------------
st.sidebar.title("Rijksmonumenten per gemeente")

# -----------------------
# Sidebar: kaartvisualisatie selecteren
# -----------------------
map_type = st.sidebar.selectbox(
    "Selecteer kaartvisualisatie",
    ('landelijke dichtheid', 'monumentlocaties per gemeente')
)

# -----------------------
# Data laden
# -----------------------
@st.cache_data
def load_geojson(path):
    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)  # CRS fix
    gdf = gdf[gdf.geometry.notnull()]
    return gdf

@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

if map_type == 'monumentlocaties per gemeente':
    monument_lookup_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "monuments_municipality_lookup.geojson"))
    
    gemeente = st.sidebar.selectbox(
        'Selecteer een gemeente',
        np.sort(monument_lookup_df['naam'].unique())
    )
    ml_mun_df = monument_lookup_df[monument_lookup_df['naam'] == gemeente].copy()

    # Center coordinaten
    x_center_coord = np.median(ml_mun_df.geometry.centroid.x)
    y_center_coord = np.mean(ml_mun_df.geometry.centroid.y)
    zoomstart = 12  # gemeente-focus

    main_categories = np.insert(np.sort(ml_mun_df['hoofdcategorie'].unique()), 0, 'Alles')

else:
    monuments_df = load_geojson(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson"))
    column_mapping_df = load_csv(os.path.join(os.getcwd(), "monuments_dashboard_data", "monument_category_column_mapping.csv"))

    main_categories = np.insert(np.sort(column_mapping_df['hoofdcategorie'].unique()), 0, 'Alles')

    # Center coordinaten
    x_center_coord = np.median(monuments_df.centroid.x)
    y_center_coord = np.mean(monuments_df.centroid.y)
    zoomstart = 7.5 # landelijke dichtheid iets verder ingezoomd

    col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]

# -----------------------
# Sidebar: categorieën
# -----------------------
st.sidebar.write("### Selecteer een monumentcategorie")
categorie = st.sidebar.selectbox("Hoofdcategorie", main_categories)

if categorie != 'Alles':
    if map_type == 'monumentlocaties per gemeente':
        ml_mun_df = ml_mun_df[ml_mun_df['hoofdcategorie'] == categorie].copy()
        sub_categories = np.insert(np.sort(ml_mun_df['subcategorie'].unique()), 0, 'Alles')
    else:
        column_mapping_df = column_mapping_df[column_mapping_df['hoofdcategorie'] == categorie].copy()
        sub_categories = np.insert(np.sort(column_mapping_df['subcategorie'].values), 0, 'Alles')

    subcategorie = st.sidebar.selectbox("Subcategorie", sub_categories)
    if subcategorie != 'Alles':
        if map_type == 'monumentlocaties per gemeente':
            ml_mun_df = ml_mun_df[ml_mun_df['subcategorie'] == subcategorie].copy()
        else:
            column_mapping_df = column_mapping_df[column_mapping_df['subcategorie'] == subcategorie].copy()

# -----------------------
# Landelijke dichtheid: berekening
# -----------------------
if map_type == 'landelijke dichtheid':
    st.sidebar.write("### Berekening")
    function = st.sidebar.selectbox("Absoluut of relatief", ('totaal aantal', 'afgerond aantal per 100.000 inwoners'))
    label_classification = st.sidebar.selectbox("Schaalverdeling kaart", ('kwartielen', 'gelijke intervals', 'machten van 10'))

    selected_columns = column_mapping_df['column_mapping']
    monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df[selected_columns].sum(axis=1)

    if function == 'afgerond aantal per 100.000 inwoners':
        monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df['aantal_monumenten_binnen_categorie'] / monuments_df['TotaleBevolking_1'] * 100000

    monuments_df['aantal_monumenten_binnen_categorie_display'] = np.round(monuments_df['aantal_monumenten_binnen_categorie'], 0)

    # Schaalverdeling
    if label_classification == 'kwartielen':
        scale = np.insert(np.quantile(monuments_df['aantal_monumenten_binnen_categorie'], q=[0.25,0.5,0.75,1]),0,0).tolist()
    elif label_classification == 'gelijke intervals':
        scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(),5).tolist()
    else:
        n_digits = len(str(int(monuments_df['aantal_monumenten_binnen_categorie'].max())))
        scale = [10**i for i in range(1,n_digits+1)]
        scale.insert(0,0)
    scale = sorted(list(set(scale)))

    legend_list = []
    for i in range(1,len(scale)):
        if (label_classification=='kwartielen') & (function=='totaal aantal'):
            numfrom = int(scale[i-1])
            numto = int(scale[i])
        else:
            numfrom = np.round(scale[i-1],1)
            numto = np.round(scale[i],1)
        legend_list.append(f"({numfrom}, {numto}]")
    legend_list.insert(0,'geen monumenten')

# -----------------------
# Folium kaart
# -----------------------
m = folium.Map(
    location=[y_center_coord, x_center_coord],
    zoom_start=zoomstart,
    tiles='CartoDB positron'  # neutrale grijstinten-kaart
)

if map_type == 'landelijke dichtheid':
    def style_function(feature):
        area = feature['properties'].get('aantal_monumenten_binnen_categorie', 0)
        if area == 0:
            color = "#cccccc"
        elif area <= scale[1]:
            color = col_list[0]
        elif area <= scale[2]:
            color = col_list[1]
        elif area <= scale[3]:
            color = col_list[2]
        elif area <= scale[4]:
            color = col_list[3]
        else:
            color = col_list[4]
        return {'fillOpacity':1, 'weight':1, 'color':'black', 'fillColor':color}

    choropleth = folium.GeoJson(
        monuments_df,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=['naam','aantal_monumenten_binnen_categorie_display'],
            aliases=['Gemeente','Aantal monumenten'],
            localize=True
        )
    )
    choropleth.add_to(m)

    # Legenda
    legend_color_list = col_list
    s1 = """{% macro html(this, kwargs) %}
    <div id='maplegend' style='position: absolute; z-index:9999; background-color:white; padding:10px; border:2px solid grey; border-radius:6px; left:20px; bottom:20px;'>
    <div class='legend-title'><b>Aantal monumenten</b></div>
    <ul class='legend-labels' style='list-style:none; margin:0; padding:0;'>"""
    s2 = f"<li style='margin-bottom:2px;'><span style='display:inline-block;width:20px;height:16px;margin-right:5px;background:#cccccc;border:1px solid #999;'></span>geen monumenten</li>"
    for i in range(1,len(legend_list)):
        color = legend_color_list[i-1] if i-1 < len(legend_color_list) else legend_color_list[-1]
        s2 += f"<li style='margin-bottom:2px;'><span style='display:inline-block;width:20px;height:16px;margin-right:5px;background:{color};border:1px solid #999;'></span>{legend_list[i]}</li>"
    s3 = "</ul></div>{% endmacro %}"
    template = "".join([s1,s2,s3])
    macro = MacroElement()
    macro._template = Template(template)
    m.add_child(macro)

else:
    for i in range(len(ml_mun_df)):
        folium.Marker(
            location=[ml_mun_df.iloc[i].geometry.y, ml_mun_df.iloc[i].geometry.x],
            popup=f'<a href="{ml_mun_df.iloc[i]["rijksmonumenturl"]}" target="_blank">Rijksmonumentnummer: {ml_mun_df.iloc[i]["rijksmonument_nummer"]}</a>',
            tooltip="Klik voor info"
        ).add_to(m)

# -----------------------
# Render kaart
# -----------------------
st_data = st_folium(m, width="100%", height=800)

# -----------------------
# Sidebar: top-gemeenten of totaal aantal
# -----------------------
if map_type == 'landelijke dichtheid':
    totaal_monumenten = monuments_df['aantal_monumenten_binnen_categorie'].sum()
    st.sidebar.markdown(f"**Totaal aantal monumenten (huidige selectie): {int(totaal_monumenten):n}**")

    mon_ordered_df = monuments_df[['naam','aantal_monumenten_binnen_categorie_display']] \
        .sort_values('aantal_monumenten_binnen_categorie_display', ascending=False) \
        .rename({'aantal_monumenten_binnen_categorie_display':'aantal'}, axis=1) \
        .reset_index(drop=True)
    mon_ordered_df.index = np.arange(1, len(mon_ordered_df)+1)
    mon_ordered_df['% van landelijk totaal'] = mon_ordered_df['aantal'] / mon_ordered_df['aantal'].sum()

    # Nederlandse notatie
    mon_ordered_df['aantal'] = mon_ordered_df['aantal'].apply(lambda x: f"{x:n}")
    mon_ordered_df['% van landelijk totaal'] = mon_ordered_df['% van landelijk totaal'].apply(
        lambda x: f"{x:.1%}".replace(".", ",").replace("%", "%"))

    st.sidebar.write("# Monumentrijkste gemeenten")
    st.sidebar.table(mon_ordered_df)

else:
    totaal_monumenten = ml_mun_df.shape[0]
    st.sidebar.markdown(f"**Totaal aantal monumenten in selectie: {totaal_monumenten:n}**")
