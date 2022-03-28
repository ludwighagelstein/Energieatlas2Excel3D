# Runs on Python 3.6.13
# Required packages:
# geopandas, pandas

from unicodedata import numeric
import geopandas as gpd
import pandas as pd
from shapely import wkt

import os

from geopy.geocoders import MapBox

import progressbar

geolocator = MapBox("pk.eyJ1IjoibHVkd2lnaGFnZWxzdGVpbiIsImEiOiJja3p3c2h3engwMTI2Mm9vM2EyYmt4cXdtIn0.LLLY4z0DXbVGE4RC3eJjOQ",timeout=20)

#xxxxxxxxxxxxxxxxxxxx
#set working directory:
wkdir = "C:/Users/Ludwig Hagelstein/Documents/Weilheim/"

#set directorys to EEG-data, PV-data, WP-data and biomass data:
pvdataEEG_path = wkdir+"eeg_anlagenregister_2015.08.utf8.csv"

pvdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_PV.csv"

wkdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_Wasserkraft.csv"

bmdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_Biomasse.csv"

# Get EEG data until 2015 for the following PLZ:
plz= '82362'
#xxxxxxxxxxxxxxxxxxxx
#---------------------------------------
def replace_all(df, dic):
    for i, j in dic.items():
        df = df.str.replace(i, j)
    return df

pvdataEEG = pd.read_csv(pvdataEEG_path,sep=';',skipfooter=3,encoding='utf-8',header=3)

pvdataEEG_Gem=pvdataEEG[pvdataEEG.PLZ ==plz]


pvdataEEG_Gem['kWh(2013)']=pvdataEEG_Gem['kWh(2013)'].str.replace('.','')
pvdataEEG_Gem['kWh(2013)']=pvdataEEG_Gem['kWh(2013)'].str.replace(',','.')

pvdataEEG_Gem['kWh(2013)']=pd.to_numeric(pvdataEEG_Gem['kWh(2013)'])
pvdataEEG_Gem.rename(columns={'# Zeilenformat: Inbetriebnahme':'Inbetriebnahme','kWh(average)':'Stromproduktion'},inplace=True)
pvdataEEG_Gem['Inbetriebnahmejahr']=pd.to_numeric(pvdataEEG_Gem['Inbetriebnahme'].str.strip().str[-4:])

#Only keep data until 2014:
typdict={'Biomasse':'Biomasse','Solarstrom':'PV (bis Juli 2015)'}
pvdataEEG_Gem['Typ'] = pvdataEEG_Gem['Anlagentyp'].map(typdict)
pvdataEEG_Gem['Y_WGS84']=pd.to_numeric(pvdataEEG_Gem['GPS-Lat'].str.replace(',','.'))
pvdataEEG_Gem['X_WGS84']=pd.to_numeric(pvdataEEG_Gem['GPS-Lon'].str.replace(',','.'))

#convert Stromproduktion to correct datatype:
repl_dic={'.':'',',':'.'}
pvdataEEG_Gem['Stromproduktion']=pd.to_numeric(replace_all(pvdataEEG_Gem['Stromproduktion'],repl_dic))

i=0
with progressbar.ProgressBar(max_value=len(pvdataEEG_Gem)) as bar:
    for idx,row in pvdataEEG_Gem.iterrows():
        location = geolocator.geocode(row['Strasse']+' '+str(row['PLZ']))
        pvdataEEG_Gem.loc[idx,'Y_WGS84'] = location.latitude
        pvdataEEG_Gem.loc[idx,'X_WGS84'] = location.longitude
        bar.update(i)
        i=i+1


#keep only relevant columns:
EEGdata_2014 = pvdataEEG_Gem[['Stromproduktion','Typ','Inbetriebnahmejahr','PLZ','Strasse','X_WGS84','Y_WGS84']]

print('MWh ges (bis 2015):',EEGdata_2014['Stromproduktion'].sum()/1000)


# PV
#---------------------------------------
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
pvdata_rel = pvdata_4326[['Stromproduktion 2019 (kWh)','Inbetriebnahmejahr','X_WGS84','Y_WGS84']].rename(columns={'Stromproduktion 2019 (kWh)':'Stromproduktion'})
pvdata_rel['Typ'] = 'PV (ab Juli 2015)'

wkdata_rel = wkdata_4326[['Leistungklasse (int)','X_WGS84','Y_WGS84']]
wkdata_rel['Typ'] = 'Wasserkraft'
wkdata_rel.rename(columns={'Leistungklasse (int)':'Stromproduktion'},inplace=True)

bmdata_rel = bmdata_4326[['Stromproduktion 2019 (kWh)','Inbetriebnahmejahr','X_WGS84','Y_WGS84']].rename(columns={'Stromproduktion 2019 (kWh)':'Stromproduktion'})
bmdata_rel['Typ'] = 'Biomasse'

frames = [pvdata_rel,wkdata_rel,bmdata_rel,EEGdata_2014]
E_erzeugung = pd.concat(frames)

E_erzeugung.to_excel(wkdir+"Stromproduktion-Energieatlas_WM.xlsx",index=False)