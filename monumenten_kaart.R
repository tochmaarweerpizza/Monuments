library(tidyverse)
library(magrittr)
library(sf)
library(httr)
library(cbsodataR)
library(RColorBrewer)
library(janitor)
library(colorspace)
library(ggthemes)
library(cowplot)
library(extrafont)

wfs_monuments <- 'https://data.geo.cultureelerfgoed.nl/openbaar/wms'
url_monuments <- parse_url(wfs_monuments)
url_monuments$query <- list(service = "WFS",
                          version = '1.3.0',
                          request = "GetFeature",
                          typeName = 'rijksmonumentpunten',
                          outputFormat = "application/json")
request_monuments <- build_url(url_monuments)
monuments_map <- st_read(request_monuments)

### Get a map of Dutch provinces. We will use the outer borders to cut out the
# correct municipal borders

wfs_pdok <- "https://geodata.nationaalgeoregister.nl/cbsgebiedsindelingen/wfs"
url_provkaart <- parse_url(wfs_pdok)

url_provkaart$query <- list(service = "wfs",
                            version = '2.0.0',
                            request = "GetFeature",
                            typeName = 'cbsgebiedsindelingen:cbs_provincie_2020_gegeneraliseerd',
                            outputFormat = "application/json")
request_provkaart <- build_url(url_provkaart)
prov_kaart <- st_read(request_provkaart)

wfs_pdok <- "https://service.pdok.nl/kadaster/bestuurlijkegebieden/wfs/v1_0"
url_gemeenten <- parse_url(wfs_pdok)

url_gemeenten$query <- list(service = "wfs",
                             version = '2.0.0',
                             request = "GetFeature",
                             typeName = 'Gemeentegebied',
                             outputFormat = "application/json")
request_gemeenten <- build_url(url_gemeenten)
boundary_map <- st_read(request_gemeenten)


category_filter_mapping <- monuments_map %>% 
  st_drop_geometry() %>% 
  select(hoofdcategorie, subcategorie) %>% 
  unique()

# We will replace the NA values in both the original map and the mapping with the label (in Dutch) 'Geen categorie'

monuments_map %<>% 
  mutate(hoofdcategorie = ifelse(is.na(hoofdcategorie), 'Geen categorie', hoofdcategorie),
         subcategorie = ifelse(is.na(subcategorie), 'Geen categorie', subcategorie))
  
  
category_filter_mapping[is.na(category_filter_mapping)] <- 'Geen categorie'

category_filter_mapping %<>% 
  mutate(column_mapping = janitor::make_clean_names(paste(hoofdcategorie, subcategorie)))


# For every municipality, we count the number of monuments within each category and subcategory
for(i in 1:nrow(category_filter_mapping)){
  
  hcat <- category_filter_mapping[i, 'hoofdcategorie']
  scat <- category_filter_mapping[i, 'subcategorie']
  print(hcat)
  print(scat)
  
  monuments_map_subset <- monuments_map %>% 
    filter(hoofdcategorie == category_filter_mapping[i, 'hoofdcategorie'],
           subcategorie == category_filter_mapping[i, 'subcategorie'])

  mun_mon <- st_intersects(boundary_map, monuments_map_subset)
  print(mun_mon)
  
  boundary_map[category_filter_mapping[i,'column_mapping']] <- lengths(mun_mon)
}

kolom_monument_gemeente <- st_intersects(monuments_map, boundary_map)


# Make a lookup table, containing municipalities and monument-urls per category
vec_monument_gemeente <- c()

for(i in 1:length(kolom_monument_gemeente)){
  elem <- kolom_monument_gemeente[[i]]
  
  if(length(elem) == 0){
    elem <- 0
  }
  
  vec_monument_gemeente <- c(vec_monument_gemeente, elem)
}


nr_name_map <- boundary_map %>% 
  st_drop_geometry() %>% 
  select(naam) %>% 
  mutate(number = row_number())


vec_monument_gemeente %>% apply(., FUN = switch(mun_names))

monuments_municipality_lookup <- monuments_map %>% 
  select('hoofdcategorie', 'subcategorie', 'rijksmonumenturl', 'rijksmonument_nummer') %>% 
#  st_drop_geometry() %>%
  add_column('gemeentenummer' = vec_monument_gemeente) %>% 
  merge(.,
      nr_name_map,
      by.x= 'gemeentenummer',
      by.y= 'number') %>% 
  st_transform(crs= 4326)

st_write(monuments_municipality_lookup, '.\\monuments_dashboard_data\\monuments_municipality_lookup.geojson', delete_dsn = TRUE)

# Next, we cut off the water parts from the polygons
nl_contours <- prov_kaart %>%
  summarise(geometry = sf::st_union(geometry))

land_boundary_map <- boundary_map %>% st_intersection(nl_contours)

# Finally, we collect population statistics for every municipality. We'll include the population in the monuments dataframe,
# allowing us to later on divide the nr of monuments by population size
cbs_municipal_pop <- cbs_get_data('70072ned', Perioden=c('2022JJ00'), RegioS = has_substring('GM'))

cbs_municipal_pop %<>% 
  select(RegioS, TotaleBevolking_1) %>% 
  na.omit()

cbs_municipal_pop$code <- cbs_municipal_pop$RegioS %>% substr(start = 3, stop = 6)

land_boundary_map %<>% 
  left_join(cbs_municipal_pop, by = c('code' = 'code'))

### We will save the land_boundary_map. This table will contain all the input
# data for our streamlit dashboard
# Additionally, we will save the category_filter_mapping object. It contains the mapping
# between the proper category names (which will be buttons in our dashboard) and
# the corresponding columns

municipalities_to_merge <- land_boundary_map[which(land_boundary_map %>% st_is('GEOMETRYCOLLECTION')),]$naam

for(municipality in municipalities_to_merge){

land_boundary_map[land_boundary_map$naam == municipality,]$geometry %<>% 
    st_collection_extract('POLYGON') %>%
    st_union()
  
}

definitive_map <- land_boundary_map %>%
  st_simplify(100, preserveTopology = T)

st_write(definitive_map, '.\\monuments_dashboard_data\\municipal_monument_count.geojson', delete_dsn = TRUE)
write_csv(category_filter_mapping, '.\\monuments_dashboard_data\\monument_category_column_mapping.csv')

#### VISUALISATIONS ###
# The part below is not needed for the streamlit dashboard, but rather a way to try and make a nice infographic

# q5 <- sequential_hcl(5, 'Lajolla')
# lettertype <- 'Tw Cen MT'
# 
# monuments_viz <- function(df = definitive_map, category){
# 
# test <- definitive_map
# 
# if (category == 'Alle categorieën') {
#   columns <- category_filter_mapping$column_mapping
# } else {
#   columns <- category_filter_mapping[category_filter_mapping$hoofdcategorie == category, 'column_mapping']
# }
# 
# 
# test['calc_column'] <- definitive_map[,columns] %>% st_drop_geometry() %>% rowSums()
# test['viz_column'] <- (test['calc_column'] / test['TotaleBevolking_1'] * 100000)[1]
# 
# test %<>% 
#   mutate(categorie = case_when(
#     viz_column == 0 ~ "geen monumenten",
#     viz_column <= 10 ~ "(0, 10]",
#     viz_column <= 100 ~ "(10, 100]",
#     viz_column <= 1000 ~ "(100, 1000]",
#     viz_column <= 10000 ~ "(1000,10000]"
#   ))
# 
# 
# categorie_kleur <- setNames(q5, 
#                             c("geen monumenten",
#                               "(0, 10]",
#                               "(10, 100]",
#                               "(100, 1000]",
#                               "(1000,10000]"))
# 
# plot_1 <- ggplot() +
#   geom_sf(data = test, mapping = aes(fill = factor(categorie), color=factor(categorie)), size = 0.25, show.legend = F) +
#   scale_fill_manual(values = categorie_kleur)  +
#   scale_color_manual(values = categorie_kleur)  +
#   geom_sf(
#     data = prov_kaart,
#     fill = "transparent",
#     color = "black",
#     size = .5
#   ) +
#   theme_void()
# 
# legend_title <- 'Aantal monumenten per \n 100.000 inwoners'
# 
# legend_input <- ggplot() +
#   geom_sf(data = test,
#           mapping = aes(fill =  factor(categorie,
#                                        ordered = TRUE,
#                                        levels = c("geen monumenten", "(0, 10]", "(10, 100]", "(100, 1000]", "(1000,10000]")),
#                         color=factor(categorie,
#                                      ordered = TRUE,
#                                      levels = c("geen monumenten", "(0, 10]", "(10, 100]", "(100, 1000]", "(1000,10000]"))), size = 0.25, show.legend = T) +
#   scale_fill_manual(values = categorie_kleur, name = legend_title)  +
#   scale_color_manual(values = categorie_kleur, name = legend_title) +
#   theme(legend.background = element_rect(fill = "white", colour = "black"), 
#         text=element_text(family=lettertype))
# 
# legend <- cowplot::get_legend(legend_input)
# 
# plot_2 <- test %>%
#   slice_max(viz_column, n=10) %>%
#   mutate(naam = fct_reorder(naam, viz_column),
#          label = str_c(naam, ':   ', round(viz_column, digits = 0))) %>%
# ggplot(mapping = aes(x = viz_column, y = naam, col = categorie, fill = categorie)) +
#   geom_col(show.legend = F, width = .1) +
#   scale_fill_manual(values = categorie_kleur) +
#   scale_color_manual(values = categorie_kleur) +
#   geom_label(
#     aes(label = round(viz_column, digits = 0)), 
#     nudge_x = -50,
#     hjust = 1,
#     size = 5, fontface = "bold", family = lettertype,
#     ## turn into white box without outline
#     fill = "white", label.size = 0
#   ) +
#   theme(text = element_text(family = lettertype, face = 'bold', size= 20),axis.line=element_blank(),axis.text.x=element_blank(),
#         axis.ticks=element_blank(),
#         axis.title.x=element_blank(),
#         axis.title.y=element_blank(),legend.position="none",
#         panel.background=element_blank(),panel.border=element_blank(),panel.grid.major=element_blank(),
#         panel.grid.minor=element_blank(),plot.background=element_blank())
# 
# 
# ggdraw()  +
# draw_plot(plot_1, x = .15, y = 0, width = .95, height = .95) +
# draw_plot(plot_2, x = 0.005, y = 0, width = 0.5, height = .9) +
# draw_plot(legend, x = .35, y = -0.375, width = 1, height = 1) +
# draw_label(str_c('Monumentdichtheid per 100.000 inwoners:\n', category),
#              fontface = 'bold', 
#              y = .95, 
#              fontfamily = lettertype,
#              size = 30) +
#   draw_text('Gemaakt door: u/tochmaarweerpizza, Bron: cultureelerfgoed.nl',
#                                  x = .5,
#                                  y = 0.02,
#                                  size = 10,
#             family = lettertype)
# 
# }
# 
# # categories <- unique(category_filter_mapping$hoofdcategorie)
# 
# # Interesting categories:
# # "Religieuze gebouwen"
# # "Woningen en woningbouwcomplexen"
# # "Boerderijen, molens en bedrijven"
# # "Kastelen, landhuizen en parken"
# # "Verdedigingswerken en militaire gebouwen"
# # "Archeologie (N)"
# # 'Alle categorieën
# 
# monuments_viz(definitive_map, "Kastelen, landhuizen en parken")
# 
# 
# -ggsave(filename = "kastelen_landhuizen_parken.png")
