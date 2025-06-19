#Client IoT per invio dati energetici da Excel al server Flask
import pandas as pd
from requests import post
import time
import threading
from datetime import datetime, timedelta
import os 

#Indirizzo del server Flask
server = 'http://192.168.1.105:8080'

# File per salvare l’indice di progresso
progress_file = 'progress.txt'

def salva_indice(i):
    with open(progress_file, 'w') as f:
        f.write(str(i))

def carica_indice():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return int(f.read().strip())
    return 0

#Carica il file excel contenente i dati energetici
xls = pd.ExcelFile('dataset.xlsx')
building = xls.parse('building_energy')

#Carica i fogli delle zone energetiche
zone_sheets = [s for s in xls.sheet_names if s.startswith('zone') and s.endswith('_energy')]
zones = {s.replace('#','').replace('_energy', ''): xls.parse(s, header=1) for s in zone_sheets}

#Numero di righe nel foglio "building_energy"
num_righe = len(building)

data_base = datetime.strptime("2024-01-01", "%Y-%m-%d")
orario_prec = None

#Funzione per inviare una riga di building
def invia_riga_building(i):
    global data_base, orario_prec
    orario = str(building.iloc[i]['time'])
    orario_dt = datetime.strptime(orario, "%H:%M:%S").time()
    if orario_prec and orario_dt < orario_prec:
        data_base += timedelta(days=1)
    orario_prec = orario_dt
    timestamp = datetime.combine(data_base.date(), orario_dt).isoformat()
    consumption = float(building.iloc[i]['consumption (w)'])  # Valore di consumo energetico
    if consumption >= 0:
        # Invio i dati al server come sensore "building"
        post(f'{server}/sensors/building', data={'time': timestamp, 'consumption (W)': consumption})

#Funzione per inviare una riga di zona
def invia_riga_zona(i, zone_name, zone_df):
    global data_base, orario_prec
    orario =str(building.iloc[i]['time'])
    orario_dt = datetime.strptime(orario, "%H:%M:%S").time()
    if orario_prec and orario_dt < orario_prec:
        data_base += timedelta(days=1)
    orario_prec = orario_dt
    timestamp = datetime.combine(data_base.date(), orario_dt).isoformat() # Tempo sincronizzato con building
    power = float(zone_df.iloc[i]['power (W)'])  # Valore di consumo energetico della zona
    if power >= 0: 
        # Invio i dati al server come sensore della zona specifica
        post(f'{server}/sensors/{zone_name}', data={'date': timestamp, 'power (W)': power, 'zone':zone_name})

#Avvio ciclo di invio
start_index = carica_indice()

#Invia simultaneamente iogni riga di building e delle zone
for i in range(start_index, num_righe):
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
    salva_indice(i+1) #Aggiorna l'indice
    time.sleep(1)
    
