from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv, filetype, base64
)
from core.config import Config
import cloudinary.uploader
from core.extensions import db
from core.models import User, BusinessBasicInfo, BusinessCredentials, SavedPhoto


business_bp = Blueprint('business', __name__)
load_dotenv()


@business_bp.route('/api/business/basic_info', methods=['POST'])
@jwt_required()
def business_registration():
    """
User Business Info Registration
---
tags:
  - Business
security:
  - Bearer: []
consumes:
  - application/json
parameters:
  - name: Authorization
    in: header
    description: "JWT token as: Bearer <your_token>"
    required: true
    type: string
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - fullname
        - home_address
        - phone
        - country
        - state
        - city
        - language
        - sex
        - DoB
        - businessName
        - businessAddress
      properties:
        fullname:
          type: string
          example: John Doe
        home_address:
          type: string
          example: 123 Main Street
        phone:
          type: string
          example: "+1234567890"
        country:
          type: string
          example: "USA"
        state:
          type: string
          example: "California"
        city:
          type: string
          example: "Los Angeles"
        language:
          type: string
          example: "English"
        sex:
          type: string
          example: "Male"
        DoB:
          type: string
          format: date
          example: "1990-01-01"
        businessName:
          type: string
          example: "My Business"
        businessAddress:
          type: string
          example: "456 Market Street"
responses:
  200:
    description: User info updated successfully
  400:
    description: Bad request
  404:
    description: User not found
    """
    # Get user ID from JWT token
    current_user_id = get_jwt_identity()
    
    data = request.json

    # Find the current user
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get the fields
    fullname = data.get('fullname')
    homeAddress = data.get('home_address')
    phone = data.get('phone')
    country = data.get('country')
    state = data.get('state')
    city = data.get('city')
    language = data.get('language')
    sex = data.get('sex')
    DoB = data.get('DateOfBirth')
    businessName = data.get('businessName')
    businessAddress = data.get('businessAddress')

    required_fields = ["fullname", "address","phone", "country", "state", "city", "language", "sex", "DoB", "businessName", "businessAddress"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    dob = None
    try:
        dob = datetime.strptime(DoB, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "dateOfBirth must be in YYYY-MM-DD format"}), 400

    business_basic_info = user.business_basic_info
    if not business_basic_info:
        business_basic_info = BusinessBasicInfo(
            user_id=user.id
        )

    # Fill the fields
    business_basic_info.fullname = fullname
    business_basic_info.homeAddress = homeAddress
    business_basic_info.phone = phone
    business_basic_info.country = country
    business_basic_info.state = state
    business_basic_info.city = city
    business_basic_info.language = language
    business_basic_info.sex = sex
    business_basic_info.DoB = DoB
    business_basic_info.businessName = businessName
    business_basic_info.businessAddress = businessAddress

    # Add if new record
    if not user.business_basic_info:
        db.session.add(business_basic_info)

    db.session.commit()
    return jsonify({"message": "User info updated successfully"}), 200


@business_bp.route("/api/business/add_credentials", methods=["POST"])
@jwt_required()
def set_business_credentials():
    """
Set User Business Credentials
---
tags:
  - Business
security:
  - Bearer: []
consumes:
  - application/json
parameters:
  - name: Authorization
    in: header
    description: "JWT token as: Bearer <your_token>"
    required: true
    type: string
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - profession
        - YearsOfExperience
        - skills
        - description
        - businessInterests
      properties:
        profession:
          type: string
          example: "Software Engineer"
        YearsOfExperience:
          type: integer
          example: 5
        skills:
          type: string
          example: "Python, Flask, SQL"
        description:
          type: string
          example: "Experienced in backend systems and cloud architecture."
        businessInterests:
          type: string
          example: "AI, SaaS, Cloud computing"
responses:
  200:
    description: Credentials updated successfully
  201:
    description: Credentials saved successfully
  400:
    description: Bad request
  404:
    description: User not found
    """
    # Get user ID from JWT token
    current_user_id = get_jwt_identity()
    data = request.json

    # Verify user exists
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    profession = data.get('profession')
    YearsOfExperience = data.get('YearsOfExperience')
    skills = data.get('skills')
    description = data.get('description')
    businessInterests = data.get('businessInterests')

    required_fields = ["profession", "YearsOfExperience", "skills", "description", "businessInterests"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    # Check if user already has preferences
    existing_credentials = BusinessCredentials.query.filter_by(user_id=current_user_id).first()
    
    if existing_credentials:
        # Update existing preferences
        existing_credentials.profession = profession
        existing_credentials.YearsOfExperience = YearsOfExperience
        existing_credentials.skills = skills
        existing_credentials.description = description
        existing_credentials.businessInterests = businessInterests
        
        message = "Credentials updated successfully"
    else:
        # Create new preferences
        new_credentials = BusinessCredentials(
            user_id=current_user_id,
            profession=profession,
            YearsOfExperience=YearsOfExperience,
            skills=skills,
            descripption=description,
            businessInterests=businessInterests
    
        )
        db.session.add(new_credentials)
        message = "Preferences saved successfully"

    db.session.commit()
    return jsonify({"message": message}), 200


@business_bp.route('/api/business/homepage', methods=['GET'])
@jwt_required()
def get_users_with_business():
    """
    Get a list of users who are business users along with their business info.
    ---
    tags:
      - Business
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
        description: List of business users with their business info
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 123
              email:
                type: string
                example: "businessuser@example.com"
              phone:
                type: string
                example: "+1234567890"
              username:
                type: string
                example: "businessuser"
              business_info:
                type: object
                properties:
                  fullname:
                    type: string
                    example: "John Doe"
                  homeAddress:
                    type: string
                    example: "123 Main St"
                  phone:
                    type: string
                    example: "+1234567890"
                  country:
                    type: string
                    example: "USA"
                  state:
                    type: string
                    example: "California"
                  city:
                    type: string
                    example: "San Francisco"
                  language:
                    type: string
                    example: "English"
                  sex:
                    type: string
                    example: "Male"
                  DoB:
                    type: string
                    format: date
                    example: "1980-01-01"
                  businessName:
                    type: string
                    example: "John's Widgets"
                  businessAddress:
                    type: string
                    example: "456 Business Rd"
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    users = User.query.join(BusinessBasicInfo).all()

    result = []
    for user in users:
        b = user.business_basic_info
        result.append(
            {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "username": user.username,
                "business_info": {
                    "fullname": b.fullname,
                    "homeAddress": b.homeAddress,
                    "phone": b.phone,
                    "country": b.country,
                    "state": b.state,
                    "city": b.city,
                    "language": b.language,
                    "sex": b.sex,
                    "DoB": b.DoB,
                    "businessName": b.businessName,
                    "businessAddress": b.businessAddress,
                }
            }
        )

    return jsonify(result), 200


@business_bp.route('/messages/contacts', methods=['GET'])
@jwt_required()
def get_message_contacts():
    """
    Get list of users the current user has messaged with
    ---
    tags:
      - Messages
    security:
      - Bearer: []
    responses:
      200:
        description: List of users the authenticated user has interacted with via messages
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 456
              username:
                type: string
                example: "jane_doe"
              email:
                type: string
                example: "jane@example.com"
              profile_pic:
                type: string
                example: "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD..."
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    current_user_id = get_jwt_identity()

    # Get all distinct user IDs the current user has had message interaction with
    sent_ids = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id)
    received_ids = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id)

    contact_ids = {row[0] for row in sent_ids.union(received_ids).distinct().all()}

    contacts = User.query.filter(User.id.in_(contact_ids)).all()

    result = []
    for user in contacts:
        profile_pic_data = None
        if user.profile_pic:
            try:
                image_bytes = base64.b64decode(user.profile_pic)
                kind = filetype.guess(image_bytes)
                extension = kind.extension if kind else "jpeg"
                profile_pic_data = f"data:image/{extension};base64,{user.profile_pic}"
            except Exception:
                profile_pic_data = None

        result.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile_pic": profile_pic_data
        })

    return jsonify(result), 200


@business_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message to another user.
    ---
    tags:
      - Messages
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - receiver_id
            - content
          properties:
            receiver_id:
              type: integer
              description: ID of the user receiving the message
              example: 456
            content:
              type: string
              description: Message content
              example: "Hello, I’d like to connect."
    responses:
      201:
        description: Message successfully sent
        schema:
          type: object
          properties:
            message:
              type: string
              example: Message sent
      404:
        description: Receiver not found
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    sender_id = get_jwt_identity()
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()

    return jsonify({"message": "Message sent"}), 201


@business_bp.route('/messages/conversation/<int:receiver_id>', methods=['GET'])
@jwt_required()
def get_conversation(receiver_id):
    """
    Retrieve the full message conversation between the authenticated user and another user.
    ---
    tags:
      - Messages
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
      - name: receiver_id
        in: path
        type: integer
        required: true
        description: ID of the other user in the conversation
        example: 456
    responses:
      200:
        description: List of messages in the conversation
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              sender_id:
                type: integer
                example: 123
              receiver_id:
                type: integer
                example: 456
              content:
                type: string
                example: "Hello, how are you?"
              timestamp:
                type: string
                format: date-time
                example: "2025-06-27T14:32:00Z"
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    sender_id = get_jwt_identity()

    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp.asc()).all()

    result = [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages
    ]
    return jsonify(result), 200


@business_bp.route('/api/photos', methods=['POST'])
@jwt_required()
def upload_photo():
    """
    Upload a photo for the authenticated user.
    ---
    tags:
      - Photos
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
        description: The photo file to upload
    responses:
      201:
        description: Photo uploaded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Uploaded!
            photo_url:
              type: string
              example: "https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg"
      400:
        description: Missing photo file
      404:
        description: User not found
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    file = request.files.get('photo')
    if not file:
        return jsonify({"error": "photo file required"}), 400

    result = cloudinary.uploader.upload(file)

    photo_url = result.get('secure_url')
    new_photo = SavedPhoto(user_id=user_id, photo_url=photo_url)
    db.session.add(new_photo)
    db.session.commit()

    return jsonify({"message": "Uploaded!", "photo_url": photo_url}), 201


@business_bp.route('/api/photos', methods=['GET'])
@jwt_required()
def list_photos():
    """
    List all uploaded photos for the authenticated user.
    ---
    tags:
      - Photos
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
        description: List of user photos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              photo_url:
                type: string
                example: "https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg"
              uploaded_at:
                type: string
                format: date-time
                example: "2025-06-27T12:34:56Z"
      404:
        description: User not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: User not found
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    photos = SavedPhoto.query.filter_by(user_id=user_id).order_by(SavedPhoto.uploaded_at.desc()).all()
    return jsonify([
        {
            "id": p.id,
            "photo_url": p.file_path,
            "uploaded_at": p.uploaded_at.isoformat()
        } for p in photos
    ]), 200
