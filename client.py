#Client IoT per invio dati energetici da Excel al server Flask
import pandas as pd
from requests import post
import time
import threading
from datetime import datetime
#Indirizzo del server Flask
server = 'http://192.168.1.48:8080'

#Carica il file excel contenente i dati energetici
xls = pd.ExcelFile('dataset.xlsx')
building = xls.parse('building_energy')

#Carica i fogli delle zone energetiche
zone_sheets = [s for s in xls.sheet_names if s.startswith('zone') and s.endswith('_energy')]
zones = {s.replace('_energy', ''): xls.parse(s, header=1) for s in zone_sheets}

#Numero di righe nel foglio "building_energy"
num_righe = len(building)

#Data di base fissa
data_base = "2024-01-01"

#Funzione per inviare una riga di building
def invia_riga_building(i):
    orario = str(building.iloc[i]['time'])
    timestamp = datetime.strptime(f"{data_base} {orario}", "%T-%m-%d %H:%M").isoformat()
    consumption = float(building.iloc[i]['consumption (w)'])  # Valore di consumo energetico
    # Invio i dati al server come sensore "building"
    post(f'{server}/sensors/building', data={'time': timestamp, 'consumption (W)': consumption})

#Funzione per inviare una riga di zona
def invia_riga_zona(i, zone_name, zone_df):
    orario =str(building.iloc[i]['time'])
    timestamp = datetime.strptime(f"{data_base} {orario}", "%Y-%m-%d %H:%M").isoformat() # Tempo sincronizzato con building
    power = float(zone_df.iloc[i]['power (W)'])  # Valore di consumo energetico della zona
    # Invio i dati al server come sensore della zona specifica
    post(f'{server}/sensors/{zone_name}', data={'date': timestamp, 'power (W)': power})

#Invia simultaneamente iogni riga di building e delle zone
for i in range(num_righe):
    # Crea un thread per inviare i dati di building
    threads =[]
    #Thread per il building
    threads.append(threading.Thread(target=invia_riga_building, args=(i,)))

    #Thread per ogni zona
    for zone_name, zone_df in zones.items():
        threads.append(threading.Thread(target=invia_riga_zona, args=(i, zone_name, zone_df)))

    #Avvia tutti i thread per la riga i
    for t in threads:
        t.start()

    # Attendi che tutti i thread siano completati
    for t in threads:
        t.join()

    #Pausa tra l'invio di ogni riga per evitare sovraccarico del server
    time.sleep(1)
    
