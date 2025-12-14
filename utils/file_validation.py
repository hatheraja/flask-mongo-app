from flask import jsonify
from bson import ObjectId
from datetime import datetime

from utils.db import get_collection
from services.cloudinary_service import CloudinaryService

cloudinary_obj = CloudinaryService()

MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
images_col = get_collection("images")

def validate_image(file):
    if not file:
        raise ValueError("Image file is required")

    if not file.mimetype.startswith("image/"):
        raise ValueError("Invalid image type")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_IMAGE_SIZE:
        raise ValueError("Image must be <= 2MB")

def upload_image(request):
    data = request.form
    image_file = request.files.get("imageFile")
    image_url = data.get("imageUrl")
    image_id = data.get("imageId")
    user_id = data.get("userId") or "system"

    # Reuse existing image
    if image_id:
        image = images_col.find_one({"_id": ObjectId(image_id)})
        if not image:
            return None, jsonify({"error": "Invalid imageId"}), 400

        return str(image["_id"]), image, None

    # Upload new image
    if image_file:
        validate_image(image_file)
        upload = cloudinary_obj.upload_image(image_file)

        image_doc = {
            "url": upload["url"], "public_id": upload["public_id"], "source": "upload", 
            "uploadedBy": user_id, "usedIn": [], "isActive": True, "createdAt": datetime.utcnow()
        }

    # External image URL
    elif image_url:
        image_doc = {
            "url": image_url, "public_id": None, "source": "external_url", "uploadedBy": user_id, 
            "usedIn": [], "isActive": True, "createdAt": datetime.utcnow()
        }

    else:
        return None, jsonify({"error": "ImageFile, ImageUrl or ImageId required"}), 400

    # INSERT ONLY ONCE
    result = images_col.insert_one(image_doc)
    image_doc["_id"] = result.inserted_id

    return str(result.inserted_id), image_doc, None

def link_image(image_id, item_id, category):
    images_col.update_one(
        {"_id": image_id},
        {"$push": {
            "usedIn": {
                "collection": "items",
                "refId": item_id,
                "category": category
            }
        }}
    )
    return True
