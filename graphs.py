import pandas as pd
import pdb
import numpy as np
import geopandas as gpd
import shapely as sp
import censusgeocode as cg
from shapely import geometry
import matplotlib.pyplot as plt
import math
import plotly.offline as pl
import plotly.express as px
import plotly.graph_objects as go
import pyproj
import pickle
from sklearn.preprocessing import minmax_scale
import orjson
import plotly.io as io

#read the geodf from our data cleaning file and make sure the geodf geometry is configured with the correct coordinate system
finaldf = pd.read_pickle(".\\data\\trees_pops_aggregated.pkl")
finaldf = gpd.GeoDataFrame(finaldf)
finaldf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

#create three dataframes from all aggregated data, one for each plotly figure
#this is important as it minimizes the amount of data passed to the plotly constructor, reducing runtime

final95 = finaldf[['geometry', 'pop2000','ntaname','ppt_2000','trees95','trees_per_block95','trees_per_block95_bins']]
#select only those census tracts which have both people and trees
final95 = final95.loc[final95['trees95'] > 0]
final95 = final95.loc[final95['pop2000'] > 0]

final05 = finaldf[['geometry', 'pop2010','ntaname','ppt_2010','trees05','trees_per_block05','trees_per_block05_bins']]
final05 = final05.loc[final05['trees05'] > 0]
final05 = final05.loc[final05['pop2010'] > 0]

final15 = finaldf[['geometry', 'pop2020','ntaname','ppt_2020','trees15','trees_per_block15','trees_per_block15_bins']]
final15 = final15.loc[final15['trees15'] > 0]
final15 = final15.loc[final15['pop2020'] > 0]

#define intervals to split the colorscale into discrete intervals that match the data
_colors = [1,10,20,30,40,50]
discretecols = px.colors.sample_colorscale('RdYlGn',minmax_scale(_colors))
# define labels for the graph legend 
labels = [' <1', ' 1 to 10', ' 11 to 20', ' 21 to 30', '31 to 40', '> 40']

#define a tiled choropleth with custom labels and legend (category) order, centered on NYC, slightly zoomed in
#and store the population, people per tree, tract name, and trees per block number in the figure so that it may be
#displayed on hover
fig95 = px.choropleth_mapbox(final95, geojson=final95.geometry, color='trees_per_block95_bins', locations = final95.index,
                    labels = {"trees_per_block95_bins": "Trees Per Block"}, title="<b> Average Trees Per Block in Each Census Tract, 1995 </b>", color_discrete_sequence=discretecols, 
                    category_orders={'trees_per_block95_bins': labels}, center = {"lat":40.730610,"lon":-73.935242}, zoom = 10, mapbox_style = 'carto-positron' , custom_data = ['pop2000','ppt_2000','ntaname','trees_per_block95'])


fig95.update_geos(fitbounds="locations", visible=False)

#edit the layout of the defined figure to have no margin, custom legend and title locations, and semi-opaque legend background
fig95.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    autosize=True,
    legend=dict(
    yanchor="top",
    y=0.89,
    xanchor="left",
    x=0.01,
    bgcolor="rgba(255,255,255,0.5)"),
    title=dict(
    xanchor="center",
    yanchor="top",
    font=dict(
        color="black"),
    y=0.95,
    x=0.51),
    font=dict(
    color='black')
)

#define a custom on_hover display box with pertinent information about each census tract
fig95.update_traces(hovertemplate="<b>%{customdata[2]} </b><br><br>" +
        '2000 Population: %{customdata[0]:,}<br>' +
        '1995 Trees per Block: %{customdata[3]:,.0f}<br>' +
        '2000 People per Tree: %{customdata[1]:,.0f}<br>' +
        '<extra></extra>')

#define the same figures for 2005 and 2015 data

fig05 = px.choropleth_mapbox(final05, geojson=final05.geometry, color='trees_per_block05_bins', locations = final05.index,
                    labels = {"trees_per_block05_bins": "Trees Per Block"}, title="<b> Average Trees Per Block in Each Census Tract, 2005 </b>", color_discrete_sequence=discretecols,
                    category_orders={'trees_per_block05_bins': labels},center = {"lat":40.730610,"lon":-73.935242},zoom = 10, mapbox_style = 'carto-positron',custom_data = ['pop2010','ppt_2010','ntaname','trees_per_block05'])

fig05.update_geos(fitbounds="locations", visible=False)
fig05.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    autosize=True,
    legend=dict(
    yanchor="top",
    y=0.89,
    xanchor="left",
    x=0.01,
    bgcolor="rgba(255,255,255,0.5)"),
    title=dict(
    xanchor="center",
    yanchor="top",
    y=0.95,
    x=0.51),
    title_font_color = 'black',
    font=dict(
    color='black')
)

fig05.update_traces(hovertemplate="<b>%{customdata[2]} </b><br><br>" +
        'Population: %{customdata[0]:,}<br>' +
        'Trees per Block: %{customdata[3]:,.0f}<br>' +
        'People per Tree: %{customdata[1]:,.0f}<br>' +
        '<extra></extra>')


fig15 = px.choropleth_mapbox(final15, geojson=final15.geometry, color='trees_per_block15_bins', locations = final15.index,
                    labels = {"trees_per_block15_bins": "Trees Per Block"}, title="<b> Average Trees Per Block in Each Census Tract, 2015 </b>", color_discrete_sequence=discretecols,
                    category_orders={'trees_per_block15_bins': labels},center = {"lat":40.730610,"lon":-73.935242},zoom = 10, mapbox_style = 'carto-positron' , custom_data = ['pop2020','ppt_2020','ntaname','trees_per_block15'])

fig15.update_geos(fitbounds="locations", visible=False)
fig15.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    paper_bgcolor="LightSteelBlue",
    plot_bgcolor="LightSteelBlue",
    autosize=True,
    legend=dict(
    yanchor="top",
    y=0.89,
    xanchor="left",
    x=0.01,
    bgcolor="rgba(255,255,255,0.5)"),
    title=dict(
    xanchor="center",
    yanchor="top",
    y=0.95,
    x=0.51),
    title_font_color = 'black',
    font=dict(
    color='black')
)

fig15.update_traces(hovertemplate="<b>%{customdata[2]} </b><br><br>" +
        'Population: %{customdata[0]:,}<br>' +
        'Trees per Block: %{customdata[3]:,.0f}<br>' +
        'People per Tree: %{customdata[1]:,.0f}<br>' +
        '<extra></extra>')



#define a fourth geodf to display cumulative changes across time

deltadf = finaldf[["ntaname", "blocks", "geometry"]]
deltadf["tree_change_95_15"] = finaldf.trees15 - finaldf.trees95
deltadf["pop_change_00_20"] = finaldf.pop2020 - finaldf.pop2000
deltadf["tpb_change_95_15"] = deltadf.tree_change_95_15/deltadf.blocks

#define additional bins and labels to discretize the cumulative data
#and define colorscale intervals that match this data

dbins = [-100,-20,-10,-5,0,5,10,20,100]
dlabels = [' Lost 20+', ' Lost 11 to 20', ' Lost 6 to 10',' Lost 0 to 5',' Gained 0 to 5', ' Gained 6 to 10', ' Gained 11 to 20',' Gained 20+']
d_colors = [1,10,20,30,40,50,60,70]
d_discretecols = px.colors.sample_colorscale('RdYlGn',minmax_scale(d_colors))

deltadf['tpb_change_95_15_bins'] = pd.cut(deltadf.tpb_change_95_15, bins=dbins, labels=dlabels, include_lowest=True)

#define a fifth geodf with NaNs replaced to pass to the hover template
f_nan = finaldf.replace(np.nan,"-")
f_nan = f_nan[['ppt_2020','ppt_2000','trees_per_block95', 'trees_per_block15']]
f_nan['pop_change_00_20'] = deltadf['pop_change_00_20'].replace(np.nan,'-')
f_nan["tree_change_95_15"] = deltadf["tree_change_95_15"].replace(np.nan,'-')

deltafig = px.choropleth_mapbox(deltadf, geojson=deltadf.geometry, color="tpb_change_95_15_bins", locations = deltadf.index,
                    labels = {"tpb_change_95_15_bins": "Trees Per Block Change"}, title="<b> Average Trees Per Block Change in Each Census Tract, 1995-2015 </b>", color_discrete_sequence=d_discretecols,
                    category_orders = {"tpb_change_95_15_bins":dlabels},center = {"lat":40.730610,"lon":-73.935242},mapbox_style = 'carto-positron', zoom = 10,
                    custom_data = [f_nan['pop_change_00_20'],f_nan['ppt_2020'],'ntaname',f_nan["tree_change_95_15"],f_nan['ppt_2000'],f_nan['trees_per_block95'],f_nan['trees_per_block15']])

deltafig.update_geos(fitbounds="locations", visible=False)
deltafig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    autosize=True,
    legend=dict(
    yanchor="top",
    y=0.89,
    xanchor="left",
    x=0.01,
    bgcolor="rgba(255,255,255,0.5)"),
    title=dict(
    xanchor="center",
    yanchor="top",
    y=0.95,
    x=0.51),
    title_font_color = 'black',
    font=dict(
    color='black')
)

#define a slightly modified hover box for this graph
deltafig.update_traces(hovertemplate="<b>%{customdata[2]} </b><br><br>" +
        'Population Change: %{customdata[0]:,} People<br>' +
        'Tree Change: %{customdata[3]:,.0f} Trees<br>' +
        '%{customdata[4]:,.0f} People per Tree, 2000<br>' +
        '%{customdata[1]:,.0f} People per Tree, 2020<br>' +
        '%{customdata[5]:,.0f} Trees per Block, 1995<br>' +
        '%{customdata[6]:,.0f} Trees per Block, 2015<br>' +
        '<extra></extra>')

#write the figures as both pickles and json files
with open(".\\data\\fig95.pkl", 'wb') as file:
	pickle.dump(fig95, file)

with open(".\\data\\fig05.pkl", 'wb') as file:
	pickle.dump(fig05, file)

with open(".\\data\\fig15.pkl", 'wb') as file:
	pickle.dump(fig15, file)

with open(".\\data\\deltafig.pkl", 'wb') as file:
	pickle.dump(deltafig, file)

with open(".\\data\\fig95.json", 'w') as file:
    io.write_json(fig95, file, engine='orjson')
    
with open(".\\data\\fig05.json", 'w') as file:
    io.write_json(fig05, file, engine='orjson')
    
with open(".\\data\\fig15.json", 'w') as file:
    io.write_json(fig15, file, engine='orjson')
    
with open(".\\data\\deltafig.json", 'w') as file:
    io.write_json(deltafig, file, engine='orjson')