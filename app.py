from flask import Flask, request, jsonify
from flask_cors import CORS
from utils.db import get_collection

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

@app.route("/")
def index():
    return {"message": "Flask + MongoDB API is running!"}

@app.route("/data", methods=["POST"])
def add_data():
    data = request.json
    collection = get_collection("users_data")
    result = collection.insert_one(data)
    return jsonify({"inserted_id": str(result.inserted_id)}), 201

@app.route("/data", methods=["GET"])
def get_data():
    collection = get_collection("users_data")
    data = list(collection.find({}))
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
