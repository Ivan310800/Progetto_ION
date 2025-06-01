from requests import post
import pandas as pd
import time

#Server di destinazione 
server = 'http://127.0.0.1:5050'
endpoint = f'{server}/data'

#Carico il file Excel
df = pd.read_excel('dataset.xlsx', sheet_name='building_energy')
df.columns = ['time', 'building_consumption', 'building_generation']

#Simulazione invio sensore:
for i, row in df.iterrows():
    data = {
        'time': row['time'] if isinstance(row['time'], str) else row['time'].strftime('%H:%M:%S'),
        'building_consumption': row['building_consumption'],
        'building_generation': row['building_generation']
    }
    try:
        response = post(endpoint, json=data)
        print(f"Inviato:{data['time']}, Status: {response.status_code}")
    except Exception as e:
        print(f'Errore nell\'invio dei dati: {e}')
    time.sleep(2)  # Simula un intervallo di 1 secondo tra gli invii
