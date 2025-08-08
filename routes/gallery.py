from core.imports import (request, re, jsonify, Blueprint, jwt_required, load_dotenv, get_jwt_identity)
import cloudinary.uploader
from core.models import SavedPhoto, User
from core.extensions import db

gallery_bp = Blueprint('gallery', __name__)
load_dotenv()

@gallery_bp.route('/api/gallery/upload', methods=['POST'])
@jwt_required()
def upload_photo():
    """
    Upload a photo to user's gallery
    ---
    tags:
      - Gallery
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: photo
        in: formData
        type: file
        required: true
        description: The image file to upload
    responses:
      201:
        description: Photo uploaded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Photo uploaded successfully
            photo_url:
              type: string
              example: https://res.cloudinary.com/demo/image/upload/v12345678/sample.jpg
      400:
        description: No file provided
      500:
        description: Upload or database error
    """
    user_id = get_jwt_identity()
    file = request.files.get('photo')

    if not file:
        return jsonify({'error': 'No file provided'}), 400

    try:
        result = cloudinary.uploader.upload(file)
        url = result['secure_url']
        print("Photo uploaded to Cloudinary")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Save to DB
    saved = SavedPhoto(user_id=user_id, photo_url=url)
    db.session.add(saved)
    db.session.commit()

    print("Saved to db")
    return jsonify({
        'message': 'Photo uploaded successfully',
        'photo_url': url
    }), 201


@gallery_bp.route('/api/gallery', methods=['GET'])
@jwt_required()
def get_photos():
    """
    Get all photos uploaded by the authenticated user
    ---
    tags:
      - Gallery
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
    responses:
      200:
        description: List of user-uploaded photos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 42
              url:
                type: string
                example: https://res.cloudinary.com/demo/image/upload/v12345678/sample.jpg
              uploaded_at:
                type: string
                format: date-time
                example: "2025-08-08T14:23:54.000Z"
      401:
        description: Unauthorized - Invalid or missing JWT
    """
    user_id = get_jwt_identity()
    photos = SavedPhoto.query.filter_by(user_id=user_id).all()

    result = [{'id': p.id, 'url': p.photo_url, 'uploaded_at': p.uploaded_at.isoformat()} for p in photos]

    return jsonify(result), 200


@gallery_bp.route('/api/gallery/delete/<int:photo_id>', methods=['DELETE'])
@jwt_required()
def delete_photo(photo_id):
    """
    Delete a photo from gallery (Cloudinary + database)
    ---
    tags:
      - Gallery
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: photo_id
        in: path
        required: true
        schema:
          type: integer
        description: ID of the photo to delete
        example: 42
    responses:
      200:
        description: Photo deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Photo deleted successfully
            deleted_photo_id:
              type: integer
              example: 42
      404:
        description: Photo not found
      400:
        description: Invalid image URL format
      500:
        description: Cloudinary or DB error
    """
    user_id = get_jwt_identity()
    photo = SavedPhoto.query.filter_by(id=photo_id, user_id=user_id).first()

    if not photo:
        return jsonify({'error': 'Photo not found'}), 404

    try:
        public_id = re.search(r'upload/(.*)\.', photo.photo_url).group(1)
    except Exception:
        return jsonify({'error': 'Invalid image URL format'}), 400

    # Delete from Cloudinary
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    # Delete from DB
    db.session.delete(photo)
    db.session.commit()

    return jsonify({'message': 'Photo deleted successfully'}), 200
