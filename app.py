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
@app.route("https://server-weld-two-29.vercel.app/token", methods=['POST'])
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
@app.route('https://server-weld-two-29.vercel.app/predict_water_quality', methods=['POST'])
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
@app.route("https://server-weld-two-29.vercel.app/register",methods=['POST'])
def register():
    email = request.json.get('email',None)
    password = request.json.get('password',None)

    if collection.find_one({'email': email}):
        return jsonify({"msg": "Email already exists"}), 400
    
    collection.insert_one({'email':email,'password':password})

    return jsonify({"msg":"Registration successful "}),201


if __name__ == '__main__':
    app.run(debug=True)
