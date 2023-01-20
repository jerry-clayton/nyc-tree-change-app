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

#function that returns a boro_ct given the borocode, length of the census tract code, and the census tract code as a string

def encode_boroct(bc, l, sct):
    bct = np.where(l == 1, bc+"000"+sct+"00",
                  np.where(l == 2, bc+"00"+sct+"00",
                  np.where(l == 3, bc+"0"+sct+"00",
                  np.where(l == 4, bc+sct+"00",
                  np.where(l == 5, bc+"0"+sct,
                  np.where(l == 6, bc+sct,
                                    "NaN"))))))
    return bct

#read tree census data
tree2015 = pd.read_csv('data\\2015_Street_Tree_Census.csv')

#read 2020 census
tracts_raw = pd.read_csv('data\\nhgis0001_csv\\nhgis0001_ds248_2020_tract.csv', encoding='latin-1')

#group trees by boro-sensitive census tract identifier. we cannot use the census tract code as codes are reused across different counties
tractcount15 = pd.DataFrame(tree2015.groupby('boro_ct').size())
tractcount15 = tractcount15.rename(columns={ 0: 'trees15'})

#read shapefile of 2010 tract designations into geodataframe (nearly the same as the 2020 designations, and those that were used in the 2015 tree census)
tractmap2010 = gpd.read_file('data\\nyc_ct\\geo_export_9f52a6ba-0521-4f32-8be0-868cc5f250d4.shp')

tractmap2010 = tractmap2010.rename(columns={ 'boro_ct201': 'boro_ct'})

#make boro_ct numeric so we can set it as the index and use pd.concat
tractmap2010['boro_ct'] = pd.to_numeric(tractmap2010['boro_ct'])
tractmap2010 = tractmap2010.set_index('boro_ct')

#read 2000 and 2010 census data and subset for NYC
tracts2000 = pd.read_csv('data\\2000_census_tracts.csv', encoding='latin-1')
tracts2010 = pd.read_csv('data\\2010_census_tracts.csv', encoding='latin-1')

tracts2000 = tracts2000.loc[(tracts2000['STATE'] == 'New York')]
tracts2010 = tracts2010.loc[(tracts2010['STATE'] == 'New York')]
tracts2000 = tracts2000.loc[(tracts2000['COUNTY'] == 'Kings') | (tracts2000['COUNTY'] == 'Queens') 
                          | (tracts2000['COUNTY'] == 'New York') | (tracts2000['COUNTY'] == 'Bronx') 
                          | (tracts2000['COUNTY'] == 'Richmond')]
tracts2010 = tracts2010.loc[(tracts2010['COUNTY'] == 'Kings County') | (tracts2010['COUNTY'] == 'Queens County') 
                          | (tracts2010['COUNTY'] == 'New York County') | (tracts2010['COUNTY'] == 'Bronx County') 
                          | (tracts2010['COUNTY'] == 'Richmond County')]

tracts2000 = tracts2000.rename(columns={'FL5001': 'pop2000'})
tracts2010 = tracts2010.rename(columns={'LGH001': 'pop2010'})

#select only the columns we need from the population data: primary key, boro (county) land area, and population
tracts2000 = tracts2000[["GISJOIN",'COUNTY','TRACTA','pop2000']]
tracts2010 = tracts2010[["GISJOIN",'COUNTY','TRACTA','pop2010']]

#use list comprehension to convert primary keys to strings so that we can merge the two datasets together
tracts2000['GISJOIN'] = [str(i) for i in tracts2000["GISJOIN"]]
tracts2010['GISJOIN'] = [str(i) for i in tracts2010["GISJOIN"]]
tracts2000 = tracts2000.set_index('GISJOIN')
tracts2010 = tracts2010.set_index('GISJOIN')


oldPops = tracts2000.merge( tracts2010, how = 'left', right_index=True, left_index = True)

#join 2010 shapefile and 2015 trees. not sure why this is being done and maybe i should take this out
countMap15 = pd.concat([tractcount15, tractmap2010], join = 'inner', axis = 1)
countMap15 = countMap15[['trees15','ntaname','ct2010']]

#subset census data for NYC and reformat
tract2020 = tracts_raw
tract2020 = tract2020.loc[(tract2020['STATE'] == 'New York')]
tract2020 = tract2020.loc[(tract2020['COUNTY'] == 'Kings County') | (tract2020['COUNTY'] == 'Queens County') 
                          | (tract2020['COUNTY'] == 'New York County') | (tract2020['COUNTY'] == 'Bronx County') 
                          | (tract2020['COUNTY'] == 'Richmond County')]

#probably also drop geoid and geocode from this list
tract2020 = tract2020.rename(columns={'U7B001': 'pop2020'})
tract2020 = tract2020[['GISJOIN','GEOID', 'GEOCODE', 'COUNTY', 'TRACTA','pop2020']]

#read 2020 census shapefile and subset it for NYC
tractmap2020 = gpd.read_file('data\\nhgis0001_shape\\nhgis0003_shapefile_tl2020_us_tract_2020\\US_tract_2020.shp')
tractmap2020 = tractmap2020.loc[tractmap2020['STATEFP'] == '36']
tractmap2020 = tractmap2020.loc[(tractmap2020['COUNTYFP'] == '005') | (tractmap2020['COUNTYFP'] == '047') |
                               (tractmap2020['COUNTYFP'] == '061') | (tractmap2020['COUNTYFP'] == '081') | 
                               (tractmap2020['COUNTYFP'] == '085')]

#change indices to use pd.concat
tract2020 = tract2020.set_index('GISJOIN')
tractmap2020 = tractmap2020.set_index('GISJOIN')

#merge 2020 population data with 2010 and 2000
populations = tract2020.merge(oldPops, how = 'left', right_index=True, left_index = True)


#merge 2020 census data with 2020 shapefile and subset land area and population
census2020 = pd.concat([populations, tractmap2020], join = 'inner', axis = 1)
census2020 = census2020[['COUNTYFP','TRACTCE','ALAND','pop2020','pop2000','pop2010','geometry']]

#generate borocodes from county codes according to census documentation
census2020['borocode'] = np.where(census2020.COUNTYFP == '005', '2',
                                 np.where(census2020.COUNTYFP == '047', '3',
                                 np.where(census2020.COUNTYFP == '061', '1',
                                 np.where(census2020.COUNTYFP == '081', '4',
                                 np.where(census2020.COUNTYFP == '085', '5'                                          
                                 ,'7')))))
#finish generating boro_ct, set it as the index of our census and shapefile data, and subset to only include land area, census tract code, populations, and geometry
census2020['boro_ct'] = census2020.borocode + census2020.TRACTCE
census2020['boro_ct'] = pd.to_numeric(census2020['boro_ct'])
census2020 = census2020.set_index('boro_ct')
census2020 = census2020[['ALAND','TRACTCE','pop2000','pop2010','pop2020','geometry']]

#read tree data for 2005 and 1995
tree2005 =  pd.read_csv('data\\2005_Street_Tree_Census.csv')
tree95 =  pd.read_csv('data\\1995_Street_Tree_Census.csv')

#this was so i didn't have to keep re-running when debugging. not sure whether or not to leave this in
tree05 = tree2005.copy()

#can certainly reduce the number of maintained columns here
tree95 = tree95[["Borough","CensusTract_2010","CensusBlock_2010","NTA_2010","SegmentID"]]
tree05 = tree05[['census tract', 'borocode','boro_ct']]

#drop trees for which there is no assigned census tract
tree05 = tree05.loc[tree05['census tract'].notnull()]
tree95 = tree95.loc[tree95.CensusTract_2010.notnull()]

#generate the columns needed to make boro_ct for each tree: the census tract code as a string, the length of this code, and the borocode as a string
tree05['sct'] = ["%.0f" % i for i in tree05['census tract'] ]
tree05['len'] = [len(i) for i in tree05['sct'] ]
tree05.borocode = [str(d) for d in tree05.borocode]

#borocode not provided for 1995 so must convert from boro name to borocode according to documentation provided
tree95['borocode'] = np.where(tree95.Borough == 'Staten Island', '5',
                     np.where(tree95.Borough == 'Queens', '4',
                     np.where(tree95.Borough == 'Brooklyn', '3',
                     np.where(tree95.Borough == 'Bronx', '2',
                     np.where(tree95.Borough == 'Manhattan', '1',
                              6)))))

tree95['sct'] = ["%.0f" % i for i in tree95['CensusTract_2010'] ]
tree95['len'] = [len(i) for i in tree95['sct'] ]

#generate borocode as string and convert to numeric so it can be set as the index.
#why did i do the numeric conversion two different ways? i should definitely pick one or explain why
tree05['boro_ct'] = encode_boroct(tree05.borocode, tree05.len, tree05.sct)
tree95['boro_ct'] = encode_boroct(tree95.borocode, tree95.len, tree95.sct)
tree95['boro_ct'] = pd.to_numeric(tree95.boro_ct)
tree05.boro_ct = [int(z) for z in pd.to_numeric(tree05.boro_ct)]

#aggregate trees according to geography
final95 = pd.DataFrame(tree95.groupby('boro_ct').size())
final05 = pd.DataFrame(tree05.groupby('boro_ct').size())
final95.rename(columns={0: 'trees95'}, inplace = True)
final05.rename(columns={0: 'trees05'}, inplace = True)

#merge all treesd together based on 2010 census tract designations (included in countMap15)
#using left joins here because we expect to have more values for more recent tree inventories than for the older ones, as 2010 census designations were retroactively added to 2005 and 1995 data
mergedTrees = pd.merge(countMap15,final05, how='left', left_index = True, right_index = True)
mergedTrees = mergedTrees.merge(final95, how ="left", left_index = True, right_index = True)

census2020['pop2020'] = pd.to_numeric(census2020.pop2020)

#remove areas with 0 population
#testing this removal - census2020 = census2020.loc[census2020['POPULATION'] > 0]

print(f"countmap size: {countMap15.trees15.count()}.  census tract size: {census2020.geometry.count()}")

#merge population and tree data, maintaining only those census tracts in which at least one tree was counted
finaldf = pd.merge(census2020, mergedTrees, left_index=True, right_index=True, how='inner')
finaldf = finaldf[["ntaname","ALAND","pop2020","pop2010","pop2000","trees15","trees05","trees95", "geometry"]]
finaldf = gpd.GeoDataFrame(finaldf)

#generate a people per tree ratio for each pair of decennial census data and the preceeding tree inventory
finaldf['ppt_2020'] = finaldf['pop2020']/finaldf['trees15']
finaldf['ppt_2010'] = finaldf['pop2010']/finaldf['trees05']
finaldf['ppt_2000'] = finaldf['pop2000']/finaldf['trees95']

#transform geometries to projection used in tree data collection
finaldf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

#define an average block size in square meters to make results more intelligible
#see this blog post for rationale behind this number: 
sqm_block = 80.4672 * 228.6

#compute num of blocks per census tract and trees per block in each tree inventory year
finaldf['blocks'] = finaldf.ALAND/sqm_block
finaldf['trees_per_block15'] = finaldf.trees15/finaldf.blocks
finaldf['trees_per_block05'] = finaldf.trees05/finaldf.blocks
finaldf['trees_per_block95'] = finaldf.trees95/finaldf.blocks

#initial investigation of the data revealed these intervals as reasonable quantiles, so we define a list of edges to discretize the continuous data and make a more striking graph using plotly
bins = [0,1,10,20,30,40,100]
#define labels that are human readable
labels = [' <1', ' 1 to 10', ' 11 to 20', ' 21 to 30', '31 to 40', '> 40']
#define colorscale intervals for our data and generate a custom discrete sequence of the red-yellow-green continuum provided by plotly
_colors = [1,10,20,30,40,50]
discretecols = px.colors.sample_colorscale('RdYlGn',minmax_scale(_colors))

#use pd.cut to generate the categorical version of our data and convert the labels to strings
finaldf['trees_per_block15_bins'] = pd.cut(finaldf.trees_per_block15, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block05_bins'] = pd.cut(finaldf.trees_per_block05, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block95_bins'] = pd.cut(finaldf.trees_per_block95, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block15_bins'] = finaldf['trees_per_block15_bins'].astype(str)
finaldf['trees_per_block05_bins'] = finaldf['trees_per_block05_bins'].astype(str)
finaldf['trees_per_block95_bins'] = finaldf['trees_per_block95_bins'].astype(str)


#almost certainly remove this block
final95 = finaldf[['geometry', 'pop2000','ntaname','ppt_2000','trees95','trees_per_block95','trees_per_block95_bins']]
final05 = finaldf[['geometry', 'pop2010','ntaname','ppt_2010','trees05','trees_per_block05','trees_per_block05_bins']]
final15 = finaldf[['geometry', 'pop2020','ntaname','ppt_2020','trees15','trees_per_block15','trees_per_block15_bins']]

#since data cleaning is done, export this geo-df as a pickle to separately debug the graph generation and app generation parts of the program 
finaldf.to_pickle(".\\data\\trees_pops_aggregated.pkl")