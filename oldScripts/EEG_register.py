# Insert PLZ (as string) to retrieve EEG Register data:
plz = '82362'

from unicodedata import numeric
import geopandas as gpd
import pandas as pd
from shapely import wkt
import os

def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

pvdata_path = "C:/Users/Ludwig Hagelstein/Documents/Weilheim/eeg_anlagenregister_2015.08.utf8.csv"

pvdata = pd.read_csv(pvdata_path,sep=';',skipfooter=3,encoding='utf-8',header=3)

pvdata_WM=pvdata[pvdata.PLZ ==plz]


pvdata_WM['kWh(2013)']=pvdata_WM['kWh(2013)'].str.replace('.','')
pvdata_WM['kWh(2013)']=pvdata_WM['kWh(2013)'].str.replace(',','.')

pvdata_WM['kWh(2013)']=pd.to_numeric(pvdata_WM['kWh(2013)'])
print('MWh ges:',pvdata_WM['kWh(2013)'].sum()/1000)