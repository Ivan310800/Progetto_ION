
import pandas as pd
import requests 
import time
import json

server = 'http://localhost:5000'

building = pd.read_excel('dataset.xlsx', sheet_name='building_energy')

#Leggere i dati dal file Excel di tutti i fogli 
zones = {}
for i in range(1, num_zones + 1):
    zone_name = f'zone_{i}_energy'
    zones[f'zone{i}'] = pd.read_excel('dataset.xlsx', sheet_name=zone_name)

# Inviare i dati al server fila per fila
for i in range(len(building)):
    try:
        data = {
            'time': building.iloc[i]['time'].isoformat(),
            'building_consumption': float(building.iloc[i]['power_consumtion']),
            'building_generation': float(building.iloc[i]['power_generation'])
        }
        for zone_name, zone_df in zones.items():
            data[f'{zone_name}_consumption'] = float(zone_df.iloc[i]['power'])

        response = requests.post(f'{server}/data', json=data)
        print(f"[{i}] Inviato: {response.status_code}")
        time.sleep(1)  # Simula un intervallo di 1 secondo tra gli invii

    except Exception as e:
        print(f'Errore nella fila {i}: {e}')