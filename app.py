from sklearn.preprocessing import minmax_scale
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
from dash import Dash, html, dcc
from dash.dependencies import Input, Output# Load Data
import pickle
from flask_caching import Cache
import orjson

#open figures that were created previously, and store them in a dictionary with keys corresponding to slider input values
file95 = open ("data/fig95.pkl", "rb")
file05 = open ("data/fig05.pkl", "rb")
file15 = open ("data/fig15.pkl", "rb")
file_d = open ("data/deltafig.pkl", "rb")

fig95 = pickle.load(file95)
fig05 = pickle.load(file05)
fig15 = pickle.load(file15)
deltafig = pickle.load(file_d)
figmap = {1995:go.Figure(fig95),2005:go.Figure(fig05),2015:go.Figure(fig15),2025:go.Figure(deltafig)}

app = Dash(__name__)
server = app.server
#set up flask caching so that figures (which are upwards of 10mb each) don't have to be re-sent to clients after initial viewing 
#OR
#to improve serverside response time

cache = Cache(server, config={
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache'
})

#build dash app which displays full-page versions of the figures
app.title = 'NYC Tree Change'
app.layout = html.Div([
    html.Div([     
    dcc.Loading(id="ls-loading-1", parent_className='loading-wrapper', children=[
        html.Div([
            html.Div([
                dcc.Slider(min=1995,max=2025,step=None, vertical = True, verticalHeight = 200,
                 value=1995 ,marks = {1995: "1995", 2005:'2005', 2015:'2015', 2025:'Δ'} ,id='year')],
                style= { 
                "position": "absolute",
                "top": "60vh",
                "left": "1.33vw",
                "z-index":"1",
                "font-family":"sans-serif",
                "font-size":"1em"
                },id="sliderDiv"),
            dcc.Graph(id='graph', figure = fig95, responsive=True,style = {"height":"100vh", "width":"100vw"})

    ],
        id='graph-container')],
    type="circle")],id="load-wrap")])

# Define callback to update graph
TIMEOUT = 120
@app.callback(
    Output('graph', 'figure'),
    [Input("year", "value")]
)
@cache.memoize(timeout=TIMEOUT)
def update_figure(year):
    return figmap[year]
    
if __name__ == '__main__':
    app.run_server()