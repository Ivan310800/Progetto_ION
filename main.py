from flask import Flask, redirect, url_for, request, render_template
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from secret import secret_key
import json
import time
from datetime import datetime
from google.cloud import storage, firestore

app = Flask(__name__)
app.config['SECRET_KEY']= secret_key
login = LoginManager(app)
login.login_view = 'login'


# Definizione del modello utente
class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.carrello_spesa = []

# Inizializzazione del client Firestore con database 'smartbuilding'
db = 'smartbuilding'
db = firestore.Client.from_service_account_json('credentials.json', database=db)

#Caricameto utente della sessione
@login.user_loader
def load_user(username):
    doc = db.collection('users').document(username).get()
    if doc.exists:
        return User(username)
    return None

#Roure di login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', next=request.args.get('next', '/graph'))
    username = request.form['u']
    password = request.form['p']
    next_page = request.form.get('next', '/graph')

    doc = db.collection('users').document(username).get()
    if doc.exists:
        user_data = doc.to_dict()
        if user_data.get('password', '') == password:
            login_user(User(username))
            return redirect(next_page)
    return render_template('login.html', error = "Login fallito", next = next_page)

#Route di logout
@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

#Route per ricevere dati da un sensore specifico 
@app.route('/sensors/building', methods=['POST'])
def new_data():
    date = request.values['time']
    consumption = float(request.values['consumption (W)'])
    entity = db.collection('sensors').document().get()
    if entity.exists:
        d = entity.to_dict()
        d['readings'].append({'date': date, 'consumption (W)': consumption})
        db.collection('sensors').document().set(d)
    else:
        db.collection('sensors').document().set({'readings': [{'date': date, 'consumption (W)': consumption}]})
    return 'ok', 200

#Route per leggere i dati di un sensore specifico
@app.route('/sensors/building', methods=['GET'])

def read():
    entity = db.collection('sensors').document().get()
    if entity.exists:
        d = entity.to_dict()
        return json.dumps(d['readings']), 200
    else:
        return 'NOT FOUND', 404
    
#Route per ricevere dati da un sensore di zona specifico
@app.route('/sensors/<zone>', methods=['POST'])
def receive_zone_data(zone):
    timestamp = request.values.get('date')
    power = float(request.values['power (W)'])
    doc_ref = db.collection(f'{zone}_energy').document()
    doc_ref.set({'zone':zone, 'date': timestamp, 'power (W)': power})
    return 'ok', 200

@app.route('/sensors/<zone>', methods=['GET'])
def get_zone_data(zone):
    docs = db.collection(f'{zone}_energy').order_by('timestamp').stream()
    results = [{'zone': zone,
                'timestamp': doc.to_dict().get('timestamp'),
                'power (W)': doc.to_dict().get('power (W)')} for doc in docs]
    return json.dumps(results), 200

    
# Route per la pagina principale
@app.route('/')
@login_required
def home():
    return redirect(url_for('graph', sensor='building'))

#Visualizzazione grafici(pagina)
@app.route('/graph')
@login_required
def graph():
    return render_template('graph.html')

#API per grafico a linee: consumo e produzione nel tempo
@app.route('/graph/building')
@login_required
def api_building():
    start = request.args.get('start')
    end = request.args.get('end')
    filtered = []
    total_consumption = 0 

    doc = db.collection('sensors').stream()
    for docs in doc:
        data = docs.to_dict()
        readings = data.get('readings', [])
        for r in readings:
            ts = r.get('date')
            if not ts:
                continue
            if (not start or ts >= start) and (not end or ts <= end):
                value= r.get('consumption (W)', 0)
                total_consumption += value
                filtered.append({
                    'time':ts,
                    'consumption': value
                })
    return json.dumps({
        'status': 'ok',
        'total_readings': len(filtered),
        'total_consumption': total_consumption,
        'data': filtered
    })
    
#API per calendar chart: consumo giornaliero totale
@app.route('/graph/consumo_giornaliero')
@login_required
def consumo_giornaliero():
    daily_consumption = {}
    doc = db.collection('sensors').stream()
    for docs in doc:
        data = docs.to_dict()
        readings = data.get('readings', [])
        for r in readings:
            timestamp= r.get('date')
            if not timestamp:
                continue
            date_only = timestamp.split('T')[0]
            consumption = r.get('consumption (W)', 0)
            daily_consumption[date_only] = daily_consumption.get(date_only, 0) + consumption
    return json.dumps(daily_consumption), 200

#API per grafico a torta: distribuzione consumo per zona
@app.route('/graph/consumo_zone')
@login_required
def consumo_zone():
    zone_totals = {f'zone{i}': 0 for i in range(1,6)}

    for zone in zone_totals:
        docs = db.collection(f'{zone}_energy').stream()
        for doc in docs:
            data = doc.to_dict()
            power = data.get('power (W)', 0) 
            zone_totals[zone] += power
    return json.dumps(zone_totals), 200

#Avvio del server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
