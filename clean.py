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

#group data by census tract identifier
tractcount15 = pd.DataFrame(tree2015.groupby('boro_ct').size())
tractcount15 = tractcount15.rename(columns={ 0: 'trees15'})

#read shapefile of 2010 tract designations into geodataframe (nearly the same as the 2020 designations, and those that were used in the 2015 tree census)
tractmap2010 = gpd.read_file('data\\nyc_ct\\geo_export_9f52a6ba-0521-4f32-8be0-868cc5f250d4.shp')

#set tract code as index so we can use pd.concat
tractmap2010 = tractmap2010.rename(columns={ 'boro_ct201': 'boro_ct'})

#make boro_ct numeric so we can set it as the index.
tractmap2010['boro_ct'] = pd.to_numeric(tractmap2010['boro_ct'])
tractmap2010 = tractmap2010.set_index('boro_ct')

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
# #tracts2000.head()
# len(tracts2010)
tracts2000 = tracts2000.rename(columns={'FL5001': 'pop2000'})
tracts2010 = tracts2010.rename(columns={'LGH001': 'pop2010'})
tracts2000 = tracts2000[["GISJOIN",'COUNTY','TRACTA','pop2000']]
tracts2010 = tracts2010[["GISJOIN",'COUNTY','TRACTA','pop2010']]
tracts2000['GISJOIN'] = [str(i) for i in tracts2000["GISJOIN"]]
tracts2010['GISJOIN'] = [str(i) for i in tracts2010["GISJOIN"]]
tracts2000 = tracts2000.set_index('GISJOIN')
tracts2010 = tracts2010.set_index('GISJOIN')




# tracts2000['sct'] = ["%.0f" % i for i in tracts2000['TRACTA'] ]
# tracts2000['len'] = [len(i) for i in tracts2000['sct'] ]
# tracts2000['boro_ct'] = encode_boroct(tracts2000.borocode, tracts2000.len, tracts2000.sct)

oldPops = tracts2000.merge( tracts2010, how = 'left', right_index=True, left_index = True)


countMap15 = pd.concat([tractcount15, tractmap2010], join = 'inner', axis = 1)
countMap15 = countMap15[['trees15','ntaname','ct2010']]

#subset census data for NYC and reformat
tract2020 = tracts_raw
tract2020 = tract2020.loc[(tract2020['STATE'] == 'New York')]
tract2020 = tract2020.loc[(tract2020['COUNTY'] == 'Kings County') | (tract2020['COUNTY'] == 'Queens County') 
                          | (tract2020['COUNTY'] == 'New York County') | (tract2020['COUNTY'] == 'Bronx County') 
                          | (tract2020['COUNTY'] == 'Richmond County')]

tract2020 = tract2020.rename(columns={'U7B001': 'POPULATION'})
tract2020 = tract2020[['GISJOIN','GEOID', 'GEOCODE', 'COUNTY', 'TRACTA','POPULATION']]

#read 2020 census shapefile and subset it for NYC
tractmap2020 = gpd.read_file('data\\nhgis0001_shape\\nhgis0003_shapefile_tl2020_us_tract_2020\\US_tract_2020.shp')
tractmap2020 = tractmap2020.loc[tractmap2020['STATEFP'] == '36']
tractmap2020 = tractmap2020.loc[(tractmap2020['COUNTYFP'] == '005') | (tractmap2020['COUNTYFP'] == '047') |
                               (tractmap2020['COUNTYFP'] == '061') | (tractmap2020['COUNTYFP'] == '081') | 
                               (tractmap2020['COUNTYFP'] == '085')]

#change indices to use pd.concat
tract2020 = tract2020.set_index('GISJOIN')
tractmap2020 = tractmap2020.set_index('GISJOIN')

allthreemerged = tract2020.merge(oldPops, how = 'left', right_index=True, left_index = True)


#merge 2020 census data with 2020 shapefile and subset land area and population
census2020 = pd.concat([allthreemerged, tractmap2020], join = 'inner', axis = 1)
census2020 = census2020[['COUNTYFP','TRACTCE','ALAND','POPULATION','pop2000','pop2010','geometry']]

census2020['borocode'] = np.where(census2020.COUNTYFP == '005', '2',
                                 np.where(census2020.COUNTYFP == '047', '3',
                                 np.where(census2020.COUNTYFP == '061', '1',
                                 np.where(census2020.COUNTYFP == '081', '4',
                                 np.where(census2020.COUNTYFP == '085', '5'                                          
                                 ,'7')))))
census2020['boro_ct'] = census2020.borocode + census2020.TRACTCE
census2020['boro_ct'] = pd.to_numeric(census2020['boro_ct'])
census2020 = census2020.set_index('boro_ct')
census2020 = census2020[['ALAND','TRACTCE','pop2000','pop2010','POPULATION','geometry']]
census2020.rename(columns = {"POPULATION":"pop2020"}, inplace = True)

tree2005 =  pd.read_csv('data\\2005_Street_Tree_Census.csv')
tree95 =  pd.read_csv('data\\1995_Street_Tree_Census.csv')
tree05 = tree2005.copy()
tree95 = tree95[["Borough","CensusTract_2010","CensusBlock_2010","NTA_2010","SegmentID"]]
tree05 =  tree05[["cb_num","borocode",'boroname','cncldist','nta','nta_name','boro_ct','latitude','longitude','census tract', 'bin', 'bbl']]
tree05 = tree05[['census tract', 'borocode','boro_ct']]
tree05 = tree05.loc[tree05['census tract'].notnull()]
tree05['sct'] = ["%.0f" % i for i in tree05['census tract'] ]
tree05['len'] = [len(i) for i in tree05['sct'] ]
tree05.borocode = [str(d) for d in tree05.borocode]
tree05['boro_ct'] = encode_boroct(tree05.borocode, tree05.len, tree05.sct)
tree95 = tree95.loc[tree95.CensusTract_2010.notnull()]
tree95['borocode'] = np.where(tree95.Borough == 'Staten Island', '5',
                     np.where(tree95.Borough == 'Queens', '4',
                     np.where(tree95.Borough == 'Brooklyn', '3',
                     np.where(tree95.Borough == 'Bronx', '2',
                     np.where(tree95.Borough == 'Manhattan', '1',
                              6)))))

tree95['sct'] = ["%.0f" % i for i in tree95['CensusTract_2010'] ]
tree95['len'] = [len(i) for i in tree95['sct'] ]
tree95['boro_ct'] = encode_boroct(tree95.borocode, tree95.len, tree95.sct)
tree95['boro_ct'] = pd.to_numeric(tree95.boro_ct)
tree05.boro_ct = [int(z) for z in pd.to_numeric(tree05.boro_ct)]
final95 = pd.DataFrame(tree95.groupby('boro_ct').size())
final05 = pd.DataFrame(tree05.groupby('boro_ct').size())
final95.rename(columns={0: 'trees95'}, inplace = True)
final05.rename(columns={0: 'trees05'}, inplace = True)
mergedTrees = pd.merge(countMap15,final05, how='left', left_index = True, right_index = True)
mergedTrees = mergedTrees.merge(final95, how ="left", left_index = True, right_index = True)

#remove areas with 0 population
census2020['pop2020'] = pd.to_numeric(census2020.pop2020)

#testing this removal - census2020 = census2020.loc[census2020['POPULATION'] > 0]

print(f"countmap size: {countMap15.trees15.count()}.  census tract size: {census2020.geometry.count()}")
finaldf = pd.merge(census2020, mergedTrees, left_index=True, right_index=True, how='inner')
finaldf = finaldf[["ntaname","ALAND","pop2020","pop2010","pop2000","trees15","trees05","trees95", "geometry"]]
finaldf = gpd.GeoDataFrame(finaldf)

finaldf['ppt_2020'] = finaldf['pop2020']/finaldf['trees15']
finaldf['ppt_2010'] = finaldf['pop2010']/finaldf['trees05']
finaldf['ppt_2000'] = finaldf['pop2000']/finaldf['trees95']

finaldf.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)

sqm_block = 80.4672 * 228.6
finaldf['blocks'] = finaldf.ALAND/sqm_block
finaldf['trees_per_block15'] = finaldf.trees15/finaldf.blocks
finaldf['trees_per_block05'] = finaldf.trees05/finaldf.blocks
finaldf['trees_per_block95'] = finaldf.trees95/finaldf.blocks
bins = [0,1,10,20,30,40,100]
labels = [' <1', ' 1 to 10', ' 11 to 20', ' 21 to 30', '31 to 40', '> 40']
_colors = [1,10,20,30,40,50]

from sklearn.preprocessing import minmax_scale
discretecols = px.colors.sample_colorscale('RdYlGn',minmax_scale(_colors))

finaldf['trees_per_block15_bins'] = pd.cut(finaldf.trees_per_block15, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block05_bins'] = pd.cut(finaldf.trees_per_block05, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block95_bins'] = pd.cut(finaldf.trees_per_block95, bins=bins, labels=labels, include_lowest=True)
finaldf['trees_per_block15_bins'] = finaldf['trees_per_block15_bins'].astype(str)
finaldf['trees_per_block05_bins'] = finaldf['trees_per_block05_bins'].astype(str)
finaldf['trees_per_block95_bins'] = finaldf['trees_per_block95_bins'].astype(str)



final95 = finaldf[['geometry', 'pop2000','ntaname','ppt_2000','trees95','trees_per_block95','trees_per_block95_bins']]
final05 = finaldf[['geometry', 'pop2010','ntaname','ppt_2010','trees05','trees_per_block05','trees_per_block05_bins']]
final15 = finaldf[['geometry', 'pop2020','ntaname','ppt_2020','trees15','trees_per_block15','trees_per_block15_bins']]

finaldf.to_pickle(".\\data\\trees_pops_aggregated.pkl")