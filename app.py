from flask import Flask, request, jsonify
import os
import pickle
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
import io
from flask_jwt_extended import create_access_token, jwt_required, JWTManager
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET')
jwt = JWTManager(app)

# Apply CORS to all routes
CORS(app)

# MongoDB connection
uri = os.environ.get('MONGODB_URI')
client = MongoClient(uri, ssl=True)
db = client['user_credentials']
collection = db['users']

# Load the model during application startup
with open('assets/model.pkl', 'rb') as f:
    model = pickle.load(f)

# Login route
@app.route("/token", methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    user = collection.find_one({'email':email,'password':password})
    if user:
        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token), 201
    else:
        return jsonify({"msg":"Bad username or Password"})

# Prediction route
@app.route('/predict_water_quality', methods=['POST'])
@jwt_required()  
def predict_water_quality():
    data = request.json
    df = pd.DataFrame(data, index=[0])
    result = model.predict(df)
    if result[0] == 1.0:
        return jsonify({"result": 'non-potable'})
    else:
        return jsonify({"result": 'potable'})

# Registration route
@app.route("/register",methods=['POST'])
def register():
    email = request.json.get('email',None)
    password = request.json.get('password',None)

    if collection.find_one({'email': email}):
        return jsonify({"msg": "Email already exists"}), 400
    
    collection.insert_one({'email':email,'password':password})

    return jsonify({"msg":"Registration successful "}),201

# Data visualization route
@app.route('/visualize_data', methods=['POST'])
def visualize_data():
    try:
        df = pd.read_csv('water_potability.csv')

        countplot = sns.countplot(x='Potability', data=df)
        countplot_img = save_plot_to_base64(countplot)

        ph_histogram = sns.histplot(data=df, x='ph', kde=True)
        ph_histogram_img = save_plot_to_base64(ph_histogram)

        all_feature_histograms = sns.pairplot(df)
        all_feature_histograms_img = save_plot_to_base64(all_feature_histograms)

        correlation_heatmap = sns.heatmap(df.corr(), annot=True)
        correlation_heatmap_img = save_plot_to_base64(correlation_heatmap)

        return jsonify({
            'countplot_img': countplot_img,
            'ph_histogram_img': ph_histogram_img,
            'all_feature_histograms_img': all_feature_histograms_img,
            'correlation_heatmap_img': correlation_heatmap_img
        })
    except FileNotFoundError:
        return jsonify({"msg": "CSV file not found"}), 404
    except Exception as e:
        return jsonify({"msg": str(e)}), 500

# Helper function to save plot to base64
def save_plot_to_base64(plot):
    buf = io.BytesIO()
    plot.figure.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

if __name__ == '__main__':
    app.run(debug=True)