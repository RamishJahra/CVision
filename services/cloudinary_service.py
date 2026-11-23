
import os
import uuid
import time

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from flask import url_for

from services.cloudinary_config import configure_cloudinary


CLOUDINARY_PREFIX = "cloudinary:"


def is_cloudinary_file(filename):
    return bool(filename and filename.startswith(CLOUDINARY_PREFIX))


def get_cloudinary_public_id(filename):
    if is_cloudinary_file(filename):
        return filename[len(CLOUDINARY_PREFIX):]
    return None


def upload_image(file, folder="cvision/images"):
    configure_cloudinary()

    if not file or not getattr(file, "filename", None):
        raise ValueError("No image was provided.")

    result = cloudinary.uploader.upload(
        file,
        folder=folder,
        resource_type="image",
        type="upload",
        public_id=uuid.uuid4().hex,
        overwrite=False
    )

    return {
        "storage": "cloudinary",
        "public_id": result["public_id"],
        "secure_url": result["secure_url"],
        "format": result.get("format"),
        "filename": CLOUDINARY_PREFIX + result["public_id"]
    }


def get_image_url(filename, local_folder="uploads/profile"):
    if not filename:
        return url_for(
            "static",
            filename=f"{local_folder}/default.png"
        )

    if is_cloudinary_file(filename):
        configure_cloudinary()

        public_id = get_cloudinary_public_id(filename)

        return cloudinary.utils.cloudinary_url(
            public_id,
            secure=True,
            resource_type="image"
        )[0]

    return url_for(
        "static",
        filename=f"{local_folder}/{filename}"
    )


def delete_file(
    public_id,
    resource_type="image",
    delivery_type="upload"
):
    configure_cloudinary()

    result = cloudinary.uploader.destroy(
        public_id,
        resource_type=resource_type,
        type=delivery_type,
        invalidate=True
    )

    return result.get("result") == "ok"


def delete_stored_image(filename, local_folder=None):
    if not filename:
        return

    if is_cloudinary_file(filename):
        public_id = get_cloudinary_public_id(filename)

        try:
            delete_file(
                public_id,
                resource_type="image",
                delivery_type="upload"
            )
        except Exception as e:
            print("Cloudinary image deletion error:", repr(e))

        return

    if local_folder:
        local_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "static",
            local_folder,
            filename
        )

        if os.path.isfile(local_path):
            try:
                os.remove(local_path)
            except Exception as e:
                print("Local image deletion error:", repr(e))


def upload_document(file, original_filename, folder="cvision/resumes"):
    configure_cloudinary()

    original_filename = os.path.basename(original_filename)
    extension = os.path.splitext(original_filename)[1].lower().lstrip(".")

    if extension not in {"pdf", "docx"}:
        raise ValueError("Only PDF and DOCX files are allowed.")

    public_id = f"{folder}/{uuid.uuid4().hex}.{extension}"

    result = cloudinary.uploader.upload(
        file,
        resource_type="raw",
        type="authenticated",
        public_id=public_id,
        overwrite=False
    )

    return {
        "storage": "cloudinary",
        "public_id": result["public_id"],
        "format": extension,
        "original_filename": original_filename,
        "filename": CLOUDINARY_PREFIX + result["public_id"]
    }


def get_private_file_url(public_id, attachment=False):
    configure_cloudinary()

    extension = os.path.splitext(public_id)[1].lower().lstrip(".")

    if extension not in {"pdf", "docx"}:
        raise ValueError("Unsupported resume format.")

    return cloudinary.utils.private_download_url(
        public_id,
        extension,
        resource_type="raw",
        type="authenticated",
        attachment=attachment,
        expires_at=int(time.time()) + 300
    )
