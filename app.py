from flask import Flask, request, jsonify
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import os

from utils.db import get_collection

from services.cloudinary_service import CloudinaryService
from utils.file_validation import validate_image, upload_image, link_image

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

cloudinary_service = CloudinaryService()

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
    # collection = get_collection("movies_data")
    collection = get_collection("items")
    items = list(collection.find({}))
    list_val = [serialize_movie(i) for i in items]
    return jsonify(list_val)

@app.route("/movies/add", methods=["POST"])
def add_movie():
    collection = get_collection("items")
    
    data = request.form
    name = data.get("name")
    category = data.get("category")
    viewUrl = data.get("viewUrl")
    downloadUrl = data.get("downloadUrl")
    
    # upload/update images in collection
    image_id, image_doc, error = upload_image(request=request)

    # creating item
    new_item = {
        "name": name, "category": category, "image": {"imageId": image_id, "url": image_doc["url"]},
        "viewUrl": viewUrl, "downloadUrl": downloadUrl,
        "createdAt": datetime.utcnow(), "updatedAt": datetime.utcnow()
    }

    item_result = collection.insert_one(new_item)
    
    # link item in image
    item_id = item_result.inserted_id
    link_image(image_id=image_id, item_id=str(item_id), category=category)

    new_item["_id"] = str(item_id)
    return jsonify(new_item), 201

@app.route("/movies/update", methods=["POST"])
def update_movie():
    collection = get_collection("items")
    images_col = get_collection("images")

    data = request.form
    item_id = data.get("_id")
    category = data.get("category")
    name =  data.get("name")
    viewUrl =  data.get("viewUrl")
    downloadUrl =  data.get("downloadUrl")

    if not item_id:
        return jsonify({"error": "Item ID required"}), 400

    existing = collection.find_one({"_id": ObjectId(item_id)})
    if not existing:
        return jsonify({"error": "Item not found"}), 404
    
    # remove old mapping
    old_image_id = existing["image"]["imageId"]
    images_col.update_one(
        {"_id": old_image_id},
        {"$pull": {"usedIn": {"refId": ObjectId(item_id)}}}
    )
    
    # upload/update images in collection
    image_id, image_doc, error = upload_image(request=request)
    link_image(image_id=old_image_id, item_id=str(item_id), category=category)

    update_fields = {
        "name": name, "category": category, "viewUrl": viewUrl, 
        "downloadUrl": downloadUrl, "updatedAt": datetime.utcnow()
    }

    if image_doc:
        update_fields["image"] = { "imageId": image_id, "url": image_doc["url"] }

    collection.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_fields}
    )

    updated = collection.find_one({"_id": ObjectId(item_id)})
    return jsonify(serialize_movie(updated)), 200

@app.route("/movies/delete", methods=["POST"])
def delete_movie():
    data = request.json
    item_id = data.get("id")

    if not item_id:
        return jsonify({"error": "Item ID required"}), 400

    collection = get_collection("items")
    images_col = get_collection("images")

    item = collection.find_one({"_id": ObjectId(item_id)})
    if not item:
        return jsonify({"error": "Item not found"}), 404

    try:
        image_id = item["image"]["imageId"]
        # remove mapping
        images_col.update_one(
            {"_id": image_id},
            {"$pull": {"usedIn": {"refId": ObjectId(item_id)}}}
        )
    except:
        print('Image is string****')

    collection.delete_one({"_id": ObjectId(item_id)})

    return jsonify({"message": "Item deleted"}), 200

@app.route("/images/get", methods=["POST"])
def get_images():
    images_col = get_collection("images")

    user_id = request.args.get("userId") or "system"

    images = list(
        images_col.find(
            {
                "uploadedBy": user_id,
                "isActive": True
            },
            {
                "public_id": 0  # DO NOT expose
            }
        ).sort("createdAt", -1)
    )

    for img in images:
        img["_id"] = str(img["_id"])

    return jsonify(images), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Use Render's PORT or fallback 5000
    app.run(host="0.0.0.0", port=port)
