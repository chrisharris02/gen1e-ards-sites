from flask import Flask, jsonify, render_template, send_from_directory
import pandas as pd
import geojson
from sklearn.preprocessing import MinMaxScaler
import random
from csvloader import main
from flask import Flask, jsonify, render_template, request, session, redirect, url_for

app = Flask(__name__)

app.secret_key = 'your_secret_key'  # Set a secret key for session encryption

PASSWORD = 'g3n13'  # Set your desired password here

def authenticate(password):
    return password == PASSWORD

def data_to_geojson(df):
    features = []
    for _, row in df.iterrows():
        geometry = geojson.Point((row["Longitude"], row["Latitude"]))
        properties = row.to_dict()
        properties.pop("Longitude")
        properties.pop("Latitude")
        features.append(geojson.Feature(geometry=geometry, properties=properties))

    return geojson.FeatureCollection(features)

@app.route('/')
def index():
    if 'authenticated' in session and session['authenticated']:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))
@app.route('/generate-data', methods=['GET', 'POST'])
def generate_data():
    if request.method == 'POST':
        toggles = request.get_json()
        print(toggles)

        df = main(toggles)
      
        return jsonify({'main': data_to_geojson(df), 'cluster': None})
    else:
        df = pd.read_csv('heatmap_coordinate_data.csv')
        return jsonify({'main': data_to_geojson(df), 'cluster': None})

@app.route('/generate-hospital-data')
def generate_hospital_data():
    df = pd.read_csv('updated_with_state_icu_normalized.csv')
    # Convert DataFrame to GeoJSON
    geojson_data = data_to_geojson(df)

    return jsonify(geojson_data)

@app.route('/images/GEn1E_Logo.png')
def return_image1():
    return send_from_directory('images','GEn1E_Logo.png',)

@app.route('/images/993762-010e3098.png')
def return_image2():
    return send_from_directory('images','993762-010e3098.png',)

@app.route('/nicepage.js')
def return_image3():
    return send_from_directory('misc','nicepage.js',)

@app.route('/nicepage.css')
def return_image4():
    return send_from_directory('misc','nicepage.css',)

@app.route('/GEn1E-ARDS-Site-Selection.css')
def return_image5():
    return send_from_directory('misc','GEn1E-ARDS-Site-Selection.css',)

@app.route('/jquery.js')
def return_image6():
    return send_from_directory('misc','jquery.js',)

@app.route('/images/2997911.png')
def return_image7():
    return send_from_directory('images','2997911.png',)

@app.route('/images/2997911-f08cb926.png')
def return_image8():
    return send_from_directory('images','2997911-f08cb926.png',)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if authenticate(password):
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Invalid password')
    else:
        return render_template('login.html', message='')

@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=80,debug=True)