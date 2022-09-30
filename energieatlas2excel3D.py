# Runs on Python 3.6.13
# Required packages:
# geopandas, pandas

import geopandas as gpd
import pandas as pd
from shapely import wkt

import os

from geopy.geocoders import MapBox

import progressbar

geolocator = MapBox("pk.eyJ1IjoibHVkd2lnaGFnZWxzdGVpbiIsImEiOiJja3p3c2h3engwMTI2Mm9vM2EyYmt4cXdtIn0.LLLY4z0DXbVGE4RC3eJjOQ",timeout=20)

#xxxxxxxxxxxxxxxxxxxx
#set working directory:
wkdir = "G:/Geteilte Ablagen/EKO/02 Dienstleistg/01 Energiekonzepte/Weilheim, Energienutzungsplan/10 Ist-Analyse/02 Energieinfrastruktur/erneuerbare Energieerzeugungsanlagen/"

#set project name
prjnm = 'Stadt-Weilheim'
# Get EEG data until 2015 for the following PLZ:
plz= '82362'

#set directorys to EEG-data, PV-data, WP-data and biomass data:
pvdataEEG_path = "G:/Geteilte Ablagen/EKO/02 Dienstleistg/01 Energiekonzepte/Daten_ENPs/EnergyMap/eeg_anlagenregister_2015.08.utf8.csv"

pvdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_PV.csv"

wkdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_Wasserkraft.csv"

bmdata_path = wkdir+"EA-B Recherche-Ergebnis_23.03.2022_Biomasse.csv"

#erhebungsjahr der daten aus Energieatlas
datayr='2019'

#xxxxxxxxxxxxxxxxxxxx
#---------------------------------------
def replace_all(df, dic):
    for i, j in dic.items():
        df = df.str.replace(i, j)
    return df

pvdataEEG = pd.read_csv(pvdataEEG_path,sep=';',skipfooter=3,encoding='utf-8',header=3,engine='python')

pvdataEEG_Gem=pvdataEEG[pvdataEEG.PLZ ==plz]


pvdataEEG_Gem['kWh(2013)']=pvdataEEG_Gem['kWh(2013)'].str.replace('.','')
pvdataEEG_Gem['kWh(2013)']=pvdataEEG_Gem['kWh(2013)'].str.replace(',','.')

pvdataEEG_Gem['kWh(2013)']=pd.to_numeric(pvdataEEG_Gem['kWh(2013)'])
pvdataEEG_Gem.rename(columns={'# Zeilenformat: Inbetriebnahme':'Inbetriebnahme','kWh(average)':'Stromproduktion'},inplace=True)
pvdataEEG_Gem['Inbetriebnahmejahr']=pd.to_numeric(pvdataEEG_Gem['Inbetriebnahme'].str.strip().str[-4:])

#adjust Format
typdict={'Biomasse':'Biomasse','Solarstrom':'PV (bis 2014)'}
pvdataEEG_Gem['Typ'] = pvdataEEG_Gem['Anlagentyp'].map(typdict)
pvdataEEG_Gem.loc[pvdataEEG_Gem['Anlagenuntertyp']=='Freifläche','Typ'] = 'Freifläche'
pvdataEEG_Gem['Y_WGS84']=pd.to_numeric(pvdataEEG_Gem['GPS-Lat'].str.replace(',','.'))
pvdataEEG_Gem['X_WGS84']=pd.to_numeric(pvdataEEG_Gem['GPS-Lon'].str.replace(',','.'))


#convert Stromproduktion to correct datatype:
repl_dic={'.':'',',':'.'}
pvdataEEG_Gem['Stromproduktion']=pd.to_numeric(replace_all(pvdataEEG_Gem['Stromproduktion'],repl_dic))

#Only keep data until 2014:
pvdataEEG_Gem = pvdataEEG_Gem.loc[pvdataEEG_Gem['Inbetriebnahmejahr'] < 2015]

i=1
# with progressbar.ProgressBar(max_value=len(pvdataEEG_Gem)) as bar:
for idx,row in pvdataEEG_Gem.iterrows():
    print('geocoding adress', i,'/',len(pvdataEEG_Gem), end='\r')
    location = geolocator.geocode(row['Strasse']+' '+str(row['PLZ']))
    pvdataEEG_Gem.loc[idx,'Y_WGS84'] = location.latitude
    pvdataEEG_Gem.loc[idx,'X_WGS84'] = location.longitude
    i=i+1
        # bar.update(i)
        # i=i+1
print('Geolocating adresses done.')



#keep only relevant columns:
EEGdata_2014 = pvdataEEG_Gem[['Stromproduktion','Typ','Inbetriebnahmejahr','PLZ','Strasse','X_WGS84','Y_WGS84']]
#aggregate same locations:
EEGdata_2014.groupby(['X_WGS84','Y_WGS84','Typ'], sort=False, as_index=False).agg({'Stromproduktion':'sum','PLZ':'first'})

print('MWh ges (bis 2014):',EEGdata_2014['Stromproduktion'].sum()/1000)


# PV
#---------------------------------------
pvdata = pd.read_csv(pvdata_path)

#set relevant column datatypes:
pvdata[['Stromproduktion '+datayr+' (kWh)','Netzeinspeisung '+datayr+' (kWh)','Eigenverbrauch '+datayr+' (kWh)','Volllaststunden pro Jahr (berechnet)']]=pvdata[['Stromproduktion '+datayr+' (kWh)','Netzeinspeisung '+datayr+' (kWh)','Eigenverbrauch '+datayr+' (kWh)','Volllaststunden pro Jahr (berechnet)']].apply(pd.to_numeric,errors='coerce')

#only keep values > 2015
pvdata_2015 = pvdata.loc[pvdata['Inbetriebnahmejahr']>2014]

# extract geometry:
pvdata_2015[['crs','geometry']] = pvdata_2015['Geometrie (EWKT)'].str.split(";",expand=True)
pvdata_2015.drop(columns='Geometrie (EWKT)',inplace=True)
pvdata_2015['crs']=pd.to_numeric(pvdata_2015['crs'].str.replace('SRID=',''))
pvdata_2015['geometry']=gpd.GeoSeries.from_wkt(pvdata_2015['geometry'])

#create WGS84 coordinates
pvdata_gdf = gpd.GeoDataFrame(pvdata_2015,crs=31468,geometry='geometry')
pvdata_4326=pvdata_gdf.to_crs(epsg=4326)
pvdata_4326['X_WGS84']=pvdata_4326.geometry.x
pvdata_4326['Y_WGS84']=pvdata_4326.geometry.y

pvdata_outpath=os.path.splitext(pvdata_path)[0]+'_WGS84.xlsx'
pvdata_4326.to_excel(pvdata_outpath)


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
wkdata_4326.to_excel(wkdata_outpath)


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
bmdata_4326.to_excel(bmdata_outpath)


# Combine datasets
#---------------------------------------
#Add type columns:
pvdata_4326['Typ'] = 'PV (ab 2015)'
pvdata_4326.loc[pvdata_4326['Freiflächenanlage']=='ja']['Typ'] = 'Freifläche'

pvdata_rel = pvdata_4326[['Stromproduktion '+datayr+' (kWh)','Inbetriebnahmejahr','Typ','X_WGS84','Y_WGS84']].rename(columns={'Stromproduktion '+datayr+' (kWh)':'Stromproduktion'})
pvdata_rel_agg = pvdata_rel.groupby(['X_WGS84', 'Y_WGS84'], sort=False, as_index=False).agg({'Stromproduktion':'sum','Typ':'first'})

wkdata_rel = wkdata_4326[['Leistungklasse (int)','X_WGS84','Y_WGS84']]
wkdata_rel['Typ'] = 'Wasserkraft'
wkdata_rel.rename(columns={'Leistungklasse (int)':'Stromproduktion'},inplace=True)

bmdata_rel = bmdata_4326[['Stromproduktion '+datayr+' (kWh)','Inbetriebnahmejahr','X_WGS84','Y_WGS84']].rename(columns={'Stromproduktion '+datayr+' (kWh)':'Stromproduktion'})
bmdata_rel['Typ'] = 'Biomasse'

frames = [pvdata_rel,bmdata_rel,EEGdata_2014,wkdata_rel]
E_erzeugung = pd.concat(frames)

E_erzeugung.to_excel(wkdir+"Stromproduktion-Energieatlas_"+prjnm+".xlsx",index=False)