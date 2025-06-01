from flask import Flask, redirect, url_for, request, render_template, jsonify, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key
import json
import time
from datetime import datetime
from google.cloud import storage, firestore

app = Flask(__name__)
app.secret_key = secret_key
login = LoginManager(app)
login.login_view = 'login'


# User model
class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.carrello_spesa = []

db = 'smartbuilding'
db = firestore.Client.from_service_account_json('credentials.json', database=db)

@login.user_loader
def load_user(username):
    doc = db.collection('users').document(username).get()
    if doc.exists:
        return User(username)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    username = request.form['u']
    password = request.form['p']
    next_page = request.form.get('next', url_for('graph'))

    doc = db.collection('users').document(username).get()
    if doc.exists:
        user_data = doc.to_dict()
        if user_data.get('password', '') == password:
            login_user(User(username))
            return redirect(next_page)
    return {"Login fallito. Riprova."}, 401

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/data', methods=['POST'])
@login_required
def receive_data():
    data = request.get_json()
    timestamp = data.get('timestamp')
    db.collection('energy_data').document(timestamp).set(data)
    return {'status': 'dato ricevuto'}


@app.route('/')
@login_required
def home():
    return redirect(url_for('graph'))

#Scrittura dei dati dei sensori
@app.route('/sensrs/<sensor>', methods=['POST'])
def new_data(sensor):
    data = request.values['date']
    val = float(request.values['val'])
    entity = db.collection('sensors').document(sensor).get()
    if entity.exists:
        d = entity
        d['readings'].append({'data':data, 'val': val})
        db.collection('sensors').document(sensor).set(d)
    else:
        db.collection('sensors').document(sensor).set({'readings': [{'data': data, 'val': val}]})
    return 'ok', 200

#Lettura dei dati dei sensori
@app.route('/sensors/<sensor>', methods=['GET'])
def read(sensor):
    entity = db.collection('sensors').document(sensor).get()
    if entity.exists:
        d = entity.to_dict()
        return json.dumps(d['readings']), 200
    else:
        return 'NOT FOUND', 404

@app.route('/graph/<sensor>')
def graph(sensor):
    entity = db.collection('sensors').document(sensor).get()
    if entity.exists:
        x = entity.to_dict()['readings']
        x2 = []
        for d in x:
            x2.append([d['data'], d['val']])
        x = str(x2)
        return render_template('graph.html', data=x, sensor=sensor)
    else:
        return 'NOT FOUND', 404
    
if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
    
'''
@app.route('/graph')
@login_required
def grapg():
    sensor = request.args.get('sensor', 'building_consumption')
    start = request.args.get('start')
    end = request.args.get('end')

    date_start = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S') if start else datetime(2000,1,1)
    date_end = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S') if end else datetime(2100,1,1)

    docs = db.collection('energy_data').order_by('timestamp').stream()

    timeseries = []
    zone_totals = {}
    calendar_data = []
    day_aggregate = {}

    sensor_options = [
        'building_consumption', 'building_generation',
        'zone1_consumption', 'zone2_consumption', 'zone3_consumption',
        'zone4_consumption', 'zone5_consumption'
    ]

    for doc in docs:
        d = doc.to_dict()
        timestamp = d.get['timestamp']
        dt = datetime.fromisoformat(timestamp)
        if not (date_start <= dt <= date_end):
            continue
            
        date_str = dt.strftime('%Y-%m-%d')
        row = [date_str]
        for s in sensor_options:
            row.append(d.get(s, 0))
        timeseries_data.append(row)

        for s in sensor_options:
            if 'zone' in s:
                zone_totals[s] = zone_totals.get(s, 0) + d.get(s, 0)

        day_aggreate[dt.date()] = day_aggregate.get(dt.date(), 0) + d.get('bulding_consumption', 0)

        pie_data = [['Zona', 'Consumo']]
        for zone, total in zone_totals.items():
            pie_data.append([zone, total])

    calendar_data = [[datetime.combine(day, datetime.mi.time()), value] for day, value in sorted(day_aggregate.items())]

    return render_template('graph.html', 
                           data = json.dumps(timeseries_data),
                           timeseries_data = json.dumps(timeseries_data), 
                           pie_data = json.dumps(pie_data), 
                           calendar_data = json.dumps(calendar_data), 
                           sensor = sensor,
                           options = sensor_options,
                           start = start or '', 
                           end = end or '')
                           
'''