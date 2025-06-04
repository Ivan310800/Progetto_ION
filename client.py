#Client IoT per invio dati energetici da Excel al server Flask
import pandas as pd
from requests import post
import time

#Indirizzo del server Flask
server = 'http://172.20.10.8:8080'

#Carica il file excel contenente i dati energetici
xls = pd.ExcelFile('dataset.xlsx')
building = xls.parse('building_energy')

#Invia i dati di consumo energetico dell'edificio
for i in range(len(building)):
    timestamp = building.iloc[i]['time'].isoformat() #Data/ora in formato ISO
    consumption = float(building.iloc[i]['consumption (w)']) #Valore di consumo energetico
    #Invio i dati al server come sensore "building"
    post(f'{server}/sensors/building', data={'time': timestamp, 'consumption (W)':consumption})
    time.sleep(2) # Attendi 2 secondi tra gli invii per evitare sovraccarico del server

#Individua e carica i fogli delle zone energetiche (zone1, zone2, zone3,...)
zone_sheets = [s for s in xls.sheet_names if s.startswith('zone') and s.endswith('_energy')]
zones = {s.replace('_energy', ''): xls.parse(s) for s in zone_sheets}

#Invia i dati di consumo energetico per ogni zona
for zone_name, zone_df in zones.items():
    for i in range(len(zone_df)):
        timestamp = building.iloc[i]['time'].isoformat() #Tempo sincronizzato con building
        val = float(zone_df.iloc[i]['power (W)']) #Valore di consumo energetico della zona
        #Invio i dati al server come sensore della zona specifica
        post(f'{server}/sensors/{zone_name}', data={'date':timestamp, 'power (W)':val})
        time.sleep(2) # Attendi 2 secondi tra gli invii per evitare sovraccarico del server