import cloudinary
import cloudinary.uploader
import cloudinary.api
import os


class CloudinaryService:
    def __init__(
        self,
        default_folder="movie-area"
    ):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True
        )

        self.default_folder = default_folder

    # -------------------------
    # Upload Image
    # -------------------------
    def upload_image(self, file, folder=None, public_id=None):
        """
        file: Flask FileStorage object
        returns: { url, public_id }
        """
        result = cloudinary.uploader.upload(
            file,
            folder=folder or self.default_folder,
            public_id=public_id,
            resource_type="image"
        )
        print(result)

        return {
            "url": result.get("secure_url"),
            "public_id": result.get("public_id")
        }

    # -------------------------
    # Delete Image
    # -------------------------
    def delete_image(self, public_id):
        """
        Delete image by public_id
        """
        if not public_id:
            return None

        return cloudinary.uploader.destroy(public_id)

    # -------------------------
    # Update Image
    # -------------------------
    def update_image(self, old_public_id, new_file, folder=None):
        """
        Replace existing image
        """
        if old_public_id:
            self.delete_image(old_public_id)

        return self.upload_image(
            new_file,
            folder=folder or self.default_folder
        )

    # -------------------------
    # Get Image Info (Optional)
    # -------------------------
    def get_image_info(self, public_id):
        return cloudinary.api.resource(public_id)
