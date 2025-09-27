from flask import Flask, request, jsonify
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import os

from utils.db import get_collection

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# --- Utility to convert ObjectId ---
def serialize_movie(movie):
    movie["_id"] = str(movie["_id"])
    return movie

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

# --- GET all movies ---
@app.route("/movies/get", methods=["GET"])
def get_movies():
    collection = get_collection("movies_data")
    movies = list(collection.find({}))
    return jsonify([serialize_movie(m) for m in movies])

@app.route("/movies/add", methods=["POST"])
def add_movie():
    data = request.json
    collection = get_collection("movies_data")

    new_movie = {
        "name": data.get("name"),
        "image": data.get("image"),
        "watchUrl": data.get("watchUrl"),
        "downloadUrl": data.get("downloadUrl"),
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }

    result = collection.insert_one(new_movie)
    new_movie["_id"] = str(result.inserted_id)
    return jsonify(new_movie), 201

# --- UPDATE movie by ID ---
@app.route("/movies/update", methods=["POST"])
def update_movie():
    data = request.json
    movie_id = data.get("_id")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400
    
    collection = get_collection("movies_data")

    update_fields = {
        "name": data.get("name"),
        "image": data.get("image"),
        "watchUrl": data.get("watchUrl"),
        "downloadUrl": data.get("downloadUrl"),
        "updatedAt": datetime.utcnow()
    }

    result = collection.update_one(
        {"_id": ObjectId(movie_id)},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Movie not found"}), 404

    updated_movie = collection.find_one({"_id": ObjectId(movie_id)})
    return jsonify(serialize_movie(updated_movie)), 200

# --- DELETE movie via POST ---
@app.route("/movies/delete", methods=["POST"])
def delete_movie():
    data = request.json
    movie_id = data.get("id")

    if not movie_id:
        return jsonify({"error": "Movie ID is required"}), 400

    collection = get_collection("movies_data")
    result = collection.delete_one({"_id": ObjectId(movie_id)})

    if result.deleted_count == 0:
        return jsonify({"error": "Movie not found"}), 404

    return jsonify({"message": "Movie deleted successfully"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT or fallback 5000
    app.run(host="0.0.0.0", port=port)
