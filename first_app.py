import os
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from branca.element import Template, MacroElement
import geopandas as gpd

st.set_page_config(
    page_title="Rijksmonumentdichtheid van Nederland",
    layout="wide",
     initial_sidebar_state="expanded")
    
# pd.set_option('display.max_colwidth', -1)

st.title("Rijksmonumenten per gemeente")

st.sidebar.write("### Selecteer kaartvisualisatie")
map_type = st.sidebar.selectbox(
    "",
    ('landelijke dichtheid', 'monumentlocaties per gemeente'))

if map_type == 'monumentlocaties per gemeente':
    
    @st.cache
    def load_data1():
        data1 = gpd.read_file(os.path.join(os.getcwd(), "monuments_dashboard_data", "monuments_municipality_lookup.geojson"))
        return data1
    
    monument_lookup_df = load_data1().copy()
    
    gemeente = st.sidebar.selectbox(
     'Selecteer een gemeente',
     (np.sort(monument_lookup_df['naam'].unique())))
    
    ml_mun_df = monument_lookup_df[monument_lookup_df['naam'] == gemeente].copy()
    
    x_center_coord = np.median(ml_mun_df.centroid.x)
    y_center_coord = np.mean(ml_mun_df.centroid.y)
    zoomstart = 12
    
    main_categories = np.insert(np.sort(ml_mun_df['hoofdcategorie'].unique()), 0, 'Alles')
    
else:
    
    @st.cache
    def load_data2():
        data2 = gpd.read_file(os.path.join(os.getcwd(), "monuments_dashboard_data", "municipal_monument_count.geojson")) 
        return data2
    
    monuments_df = load_data2().copy()
    
    @st.cache
    def load_data3():
        data3 = pd.read_csv(os.path.join(os.getcwd(), "monuments_dashboard_data", "monument_category_column_mapping.csv"))
        return data3

    column_mapping_df = load_data3().copy()
    
    main_categories = np.insert(np.sort(column_mapping_df['hoofdcategorie'].unique()), 0, 'Alles')
    
    x_center_coord = np.median(monuments_df.centroid.to_crs('epsg:4326').x)
    y_center_coord = np.mean(monuments_df.centroid.to_crs('epsg:4326').y)
    zoomstart = 7
    
    col_list = ["#FCFFC9", "#E8C167", "#D67500", "#913640", "#1D0B14"]

st.sidebar.write("### Selecteer een monumentcategorie")
categorie = st.sidebar.selectbox(
    "Hoofdcategorie",
    (main_categories))

if categorie != 'Alles':
    if map_type == 'monumentlocaties per gemeente':
        ml_mun_df = ml_mun_df[ml_mun_df['hoofdcategorie'] == categorie].copy()
        sub_categories = np.insert(np.sort(ml_mun_df['subcategorie'].unique()), 0, 'Alles')
        
    else:
        column_mapping_df = column_mapping_df[column_mapping_df['hoofdcategorie'] == categorie].copy()
        sub_categories = np.insert(np.sort(column_mapping_df['subcategorie'].values), 0, 'Alles')
        
    subcategorie = st.sidebar.selectbox(
    "Subcategorie",
    (sub_categories))
    
    if subcategorie != 'Alles':
        if map_type == 'monumentlocaties per gemeente':
            ml_mun_df = ml_mun_df[ml_mun_df['subcategorie'] == subcategorie].copy()
        else:
            column_mapping_df = column_mapping_df[column_mapping_df['subcategorie'] == subcategorie].copy()

if map_type == 'landelijke dichtheid':            
            
    st.sidebar.write("### Selecteer berekening")
    function = st.sidebar.selectbox(
        "Absoluut of relatief",
        ('totaal aantal', 'afgerond aantal per 100.000 inwoners'))

    label_classification = st.sidebar.selectbox(
        "Schaalverdeling kaart",
        ('kwartielen', 'machten van 10', 'gelijke intervals'))

    selected_columns = column_mapping_df['column_mapping']

    monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df[selected_columns].sum(axis = 1)

    if function == 'afgerond aantal per 100.000 inwoners':
        monuments_df['aantal_monumenten_binnen_categorie'] = monuments_df['aantal_monumenten_binnen_categorie'] / monuments_df['TotaleBevolking_1'] * 100000
        
    monuments_df['aantal monumenten'] = np.round(monuments_df['aantal_monumenten_binnen_categorie'],0)

    if label_classification == 'kwartielen':
        scale = np.insert(np.quantile(monuments_df['aantal_monumenten_binnen_categorie'], q = [.25, .5, .75, 1]), 0, 0).tolist()

    elif label_classification == 'gelijke intervals':
        scale = np.linspace(0, monuments_df['aantal_monumenten_binnen_categorie'].max(), 5).tolist()
    else:
        n_digits = len(str(int(monuments_df['aantal_monumenten_binnen_categorie'].max())))
        scale = [10**i for i in range(1,n_digits + 1)]
        scale.insert(0, 0)
        
    scale  =  sorted(list(set(scale)))
    legend_list = []
    for i in range(1,len(scale)):
        
        if (label_classification == 'kwartielen') & (function == 'totaal aantal'):
            numfrom = int(scale[i-1])
            numto = int(scale[i])
        else:
            numfrom = np.round(scale[i-1], 1)
            numto = np.round(scale[i], 1)
    
        legend_list.append("".join(['(', str(numfrom), ', ', str(numto), ']']))
    legend_list.insert(0, 'geen monumenten')
        
#     monuments_df['FillColor'] = None
#     for i in range(len(scale)):
#         monuments_df[monuments_df['aantal_monumenten_binnen_categorie'] <= scale[i]]['FillColor'] = i
#     monuments_df['FillColor'] = [random.choice(range(5)) for i in range(len(monuments_df))]
    

# f = folium.Figure(width=700, height = 500)

m = folium.Map(zoom_start=zoomstart,
               location = [y_center_coord, x_center_coord],
               tiles='https://api.mapbox.com/styles/v1/ivo11235/ckjx01y2e1brw17nqdictt5wk/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1IjoiaXZvMTEyMzUiLCJhIjoieV82bFVfNCJ9.G8mrfJOA07edDDj6Bep2bQ',
               attr='© <a href="https://www.mapbox.com/about/maps/">Mapbox</a> © <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> <a href="https://www.mapbox.com/map-feedback/">(Improve this map)</a>'
)
# .add_to(f)

if map_type == 'landelijke dichtheid':

    def style_function(feature):
        area = int(feature['properties']['aantal_monumenten_binnen_categorie'])
        return {
            'fillOpacity': 1,
            'weight': 1,
            'color': 'black',
            'fillColor': col_list[0] if area <= scale[0] \
                   else col_list[1] if area <= scale[1] \
                   else col_list[2] if area <= scale[2] \
                   else col_list[3] if area <= scale[3] \
                   else col_list[4]}
    
    choropleth = folium.GeoJson(monuments_df, 
                       style_function=style_function
                      ).add_to(m)

    choropleth.add_child(
    folium.features.GeoJsonTooltip(['naam', 'aantal monumenten'])
    )
        
    choropleth.add_to(m)
    
    s1 = """{% macro html(this, kwargs) %}

<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>jQuery UI Draggable - Default functionality</title>
  <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

  <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
  <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>
  
  <script>
  $( function() {
    $( "#maplegend" ).draggable({
                    start: function (event, ui) {
                        $(this).css({
                            right: "auto",
                            top: "auto",
                            bottom: "auto"
                        });
                    }
                });
});

  </script>
</head>
<body>

 
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
     border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
     
<div class='legend-title'>Aantal monumenten (o.b.v. berekening)</div>
<div class='legend-scale'>
  <ul class='legend-labels'>"""
    
    legls = ""
    for i in range(len(legend_list)):
        legls = legls + "<li><span style='background:{};opacity:1;'></span>{}</li>".format(col_list[i],
                                                                                             legend_list[i])
    s2 = legls

    s3 = """</ul>
</div>
</div>
 
</body>
</html>

<style type='text/css'>
  .maplegend .legend-title {
    text-align: left;
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 90%;
    }
  .maplegend .legend-scale ul {
    margin: 0;
    margin-bottom: 5px;
    padding: 0;
    float: left;
    list-style: none;
    }
  .maplegend .legend-scale ul li {
    font-size: 80%;
    list-style: none;
    margin-left: 0;
    line-height: 18px;
    margin-bottom: 2px;
    }
  .maplegend ul.legend-labels li span {
    display: block;
    float: left;
    height: 16px;
    width: 30px;
    margin-right: 5px;
    margin-left: 0;
    border: 1px solid #999;
    }
  .maplegend .legend-source {
    font-size: 80%;
    color: #777;
    clear: both;
    }
  .maplegend a {
    color: #777;
    }
</style>
{% endmacro %}"""
    
    
    template = "".join([s1,s2, s3])


    macro = MacroElement()
    macro._template = Template(template)

    m.add_child(macro)
    
else:
    for i in range(len(ml_mun_df)):
        
        marker = folium.Marker(
        location=[ml_mun_df.iloc[i].geometry.y, ml_mun_df.iloc[i].geometry.x],
            popup='<a href="{}" target="_blank">Rijksmonumentnummer: {}</a>'.format(ml_mun_df.iloc[i]['rijksmonumenturl'], ml_mun_df.iloc[i]['rijksmonument_nummer']),
            tooltip = "Klik voor informatie"
        )

        marker.add_to(m)


folium_static(m, height = 750)

if map_type == 'landelijke dichtheid':
    
    st.sidebar.write("# Aantallen op volgorde")
    
    mon_ordered_df = monuments_df[['naam', 'aantal_monumenten_binnen_categorie']].sort_values('aantal_monumenten_binnen_categorie', ascending = False).set_index(np.arange(1, len(monuments_df) + 1)).rename({'aantal_monumenten_binnen_categorie': 'aantal'}, axis = 1).copy()
    
    if function == 'totaal aantal':
        mon_ordered_df['% van landelijk totaal'] = (mon_ordered_df['aantal'] / 
                  mon_ordered_df['aantal'].sum())
        
        aantal_format = {"aantal":"{:.0f}", '% van landelijk totaal': '{:,.1%}'}
    else:
        aantal_format = {"aantal":"{:.1f}", '% van landelijk totaal': '{:,.1%}'}
        

    
    st.sidebar.table(mon_ordered_df.style.format(aantal_format))
