# Runs on Python 3.6.13
# Required packages:
# geopandas, pandas

from unicodedata import numeric
import geopandas as gpd
import pandas as pd
from shapely import wkt
import os


# PV
#---------------------------------------
pvdata_path = "C:/Users/Ludwig Hagelstein/Documents/Weilheim/EA-B Recherche-Ergebnis_23.03.2022_PV.csv"

pvdata = pd.read_csv(pvdata_path)

#set relevant column datatypes:
pvdata[['Stromproduktion 2019 (kWh)','Netzeinspeisung 2019 (kWh)','Eigenverbrauch 2019 (kWh)','Volllaststunden pro Jahr (berechnet)']]=pvdata[['Stromproduktion 2019 (kWh)','Netzeinspeisung 2019 (kWh)','Eigenverbrauch 2019 (kWh)','Volllaststunden pro Jahr (berechnet)']].apply(pd.to_numeric,errors='coerce')

# extract geometry:
pvdata[['crs','geometry']] = pvdata['Geometrie (EWKT)'].str.split(";",expand=True)
pvdata.drop(columns='Geometrie (EWKT)',inplace=True)
pvdata['crs']=pd.to_numeric(pvdata['crs'].str.replace('SRID=',''))
pvdata['geometry']=gpd.GeoSeries.from_wkt(pvdata['geometry'])

#create WGS84 coordinates
pvdata_gdf = gpd.GeoDataFrame(pvdata,crs=31468,geometry='geometry')
pvdata_4326=pvdata_gdf.to_crs(epsg=4326)
pvdata_4326['X_WGS84']=pvdata_4326.geometry.x
pvdata_4326['Y_WGS84']=pvdata_4326.geometry.y

pvdata_outpath=os.path.splitext(pvdata_path)[0]+'_WGS84.xlsx'
pvdata_4326.to_excel(os.path.basename(pvdata_outpath))


# Wasserkraft
#---------------------------------------
wkdata_path = "C:/Users/Ludwig Hagelstein/Documents/Weilheim/EA-B Recherche-Ergebnis_23.03.2022_Wasserkraft.csv"

wkdata = pd.read_csv(wkdata_path)

# extract geometry:
wkdata[['crs','geometry']] = wkdata['Geometrie (EWKT)'].str.split(";",expand=True)
wkdata.drop(columns='Geometrie (EWKT)',inplace=True)
wkdata['crs']=pd.to_numeric(wkdata['crs'].str.replace('SRID=',''))
wkdata['geometry']=gpd.GeoSeries.from_wkt(wkdata['geometry'])

#create WGS84 coordinates
wkdata_gdf = gpd.GeoDataFrame(wkdata,crs=31468,geometry='geometry')
wkdata_4326=wkdata_gdf.to_crs(epsg=4326)
wkdata_4326['X_WGS84']=wkdata_4326.geometry.x
wkdata_4326['Y_WGS84']=wkdata_4326.geometry.y

#add Leistungklasse (int)
for idx,row in wkdata_4326.iterrows():
    if wkdata_4326.loc[idx,'Leistungsklasse (kW)']=='0 - 500 kW':
        wkdata_4326.loc[idx,'Leistungklasse (int)']=500
    else:
        wkdata_4326.loc[idx,'Leistungklasse (int)']=10


wkdata_outpath=os.path.splitext(wkdata_path)[0]+'_WGS84.xlsx'
wkdata_4326.to_excel(os.path.basename(wkdata_outpath))


# Biomasse
#---------------------------------------
bmdata_path = "C:/Users/Ludwig Hagelstein/Documents/Weilheim/EA-B Recherche-Ergebnis_23.03.2022_Biomasse.csv"

bmdata = pd.read_csv(bmdata_path)

# extract geometry:
bmdata[['crs','geometry']] = bmdata['Geometrie (EWKT)'].str.split(";",expand=True)
bmdata.drop(columns='Geometrie (EWKT)',inplace=True)
bmdata['crs']=pd.to_numeric(bmdata['crs'].str.replace('SRID=',''))
bmdata['geometry']=gpd.GeoSeries.from_wkt(bmdata['geometry'])

#create WGS84 coordinates
bmdata_gdf = gpd.GeoDataFrame(bmdata,crs=31468,geometry='geometry')
bmdata_4326=bmdata_gdf.to_crs(epsg=4326)
bmdata_4326['X_WGS84']=bmdata_4326.geometry.x
bmdata_4326['Y_WGS84']=bmdata_4326.geometry.y

bmdata_outpath=os.path.splitext(bmdata_path)[0]+'_WGS84.xlsx'
bmdata_4326.to_excel(os.path.basename(bmdata_outpath))


# Combine datasets
#---------------------------------------
#Add type columns:
pvdata_rel = pvdata_4326[['Stromproduktion 2019 (kWh)','X_WGS84','Y_WGS84']]
pvdata_rel['Typ'] = 'Photovoltaik'


wkdata_rel = wkdata_4326[['Leistungklasse (int)','X_WGS84','Y_WGS84']]
wkdata_rel['Typ'] = 'Wasserkraft'
wkdata_rel.rename(columns={'Leistungklasse (int)':'Stromproduktion 2019 (kWh)'},inplace=True)

bmdata_rel = bmdata_4326[['Stromproduktion 2019 (kWh)','X_WGS84','Y_WGS84']]
bmdata_rel['Typ'] = 'Biomasse'

frames = [pvdata_rel,wkdata_rel,bmdata_rel]
E_erzeugung = pd.concat(frames)

E_erzeugung.to_excel("C:/Users/Ludwig Hagelstein/Documents/Weilheim/Stromproduktion-Energieatlas_WM_2019.xlsx",index=False)