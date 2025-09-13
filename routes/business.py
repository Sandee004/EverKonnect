from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv, filetype, base64
)
from core.config import Config
import cloudinary.uploader
from core.extensions import db
from core.models import User, BusinessBasicInfo, BusinessCredentials, SavedPhoto, Message, BusinessAnonymous


business_bp = Blueprint('business', __name__)
load_dotenv()


@business_bp.route('/api/business/basic_info', methods=['POST'])
@jwt_required()
def create_business_basic_info():
    """
    Create Business Basic Info
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
      201:
        description: Business info created successfully
      400:
        description: Bad request or business info already exists
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.business_basic_info:
        return jsonify({"message": "Business info already exists. Use PUT to update."}), 400

    data = request.json
    required_fields = ["fullname", "home_address", "phone", "country", "state", "city", "language", "sex", "DoB", "businessName", "businessAddress"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    try:
        dob = datetime.strptime(data["DoB"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "DoB must be in YYYY-MM-DD format"}), 400

    business_basic_info = BusinessBasicInfo(
        user_id=user.id,
        fullname=data["fullname"],
        homeAddress=data["home_address"],
        phone=data["phone"],
        country=data["country"],
        state=data["state"],
        city=data["city"],
        language=data["language"],
        sex=data["sex"],
        DoB=dob,
        businessName=data["businessName"],
        businessAddress=data["businessAddress"]
    )
    db.session.add(business_basic_info)

    user.account_type = "business"
    db.session.commit()
    return jsonify({"message": "Business info created successfully"}), 201


@business_bp.route('/api/business/basic_info', methods=['PUT'])
@jwt_required()
def update_business_basic_info():
    """
    Update Business Basic Info
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
            links:
              type: array
              items:
                type: string
              example: ["https://mybusiness.com", "https://instagram.com/mybiz"]
    responses:
      200:
        description: Business info updated successfully
      400:
        description: Bad request
      404:
        description: User or business info not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    business_basic_info = user.business_basic_info
    if not business_basic_info:
        return jsonify({"message": "Business info not found. Use POST to create."}), 404

    data = request.json
    try:
        dob_str = data.get("DoB")
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else business_basic_info.DoB
    except (ValueError, TypeError):
        return jsonify({"message": "DoB must be in YYYY-MM-DD format"}), 400

    business_basic_info.fullname = data.get("fullname", business_basic_info.fullname)
    business_basic_info.homeAddress = data.get("home_address", business_basic_info.homeAddress)
    business_basic_info.phone = data.get("phone", business_basic_info.phone)
    business_basic_info.country = data.get("country", business_basic_info.country)
    business_basic_info.state = data.get("state", business_basic_info.state)
    business_basic_info.city = data.get("city", business_basic_info.city)
    business_basic_info.language = data.get("language", business_basic_info.language)
    business_basic_info.sex = data.get("sex", business_basic_info.sex)
    business_basic_info.DoB = dob
    business_basic_info.businessName = data.get("businessName", business_basic_info.businessName)
    business_basic_info.businessAddress = data.get("businessAddress", business_basic_info.businessAddress)

    # ✅ New: handle links
    if "links" in data:
        if isinstance(data["links"], list):
            business_basic_info.links = data["links"]
        else:
            return jsonify({"message": "links must be a list of strings"}), 400

    db.session.commit()
    return jsonify({"message": "Business info updated successfully"}), 200


@business_bp.route("/api/business/credentials", methods=["POST"])
@jwt_required()
def create_business_credentials():
    """
    Create User Business Credentials
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
      201:
        description: Credentials saved successfully
      400:
        description: Bad request or credentials already exist
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    if BusinessCredentials.query.filter_by(user_id=current_user_id).first():
        return jsonify({"message": "Credentials already exist. Use PUT to update."}), 400

    data = request.json
    required_fields = ["profession", "YearsOfExperience", "skills", "description", "businessInterests"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    new_credentials = BusinessCredentials(
        user_id=current_user_id,
        profession=data["profession"],
        YearsOfExperience=data["YearsOfExperience"],
        skills=data["skills"],
        description=data["description"],
        businessInterests=data["businessInterests"]
    )

    db.session.add(new_credentials)
    db.session.commit()
    return jsonify({"message": "Credentials saved successfully"}), 201


@business_bp.route("/api/business/credentials", methods=["PUT"])
@jwt_required()
def update_business_credentials():
    """
    Update User Business Credentials
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
      400:
        description: Bad request
      404:
        description: User or credentials not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    credentials = BusinessCredentials.query.filter_by(user_id=current_user_id).first()
    if not credentials:
        return jsonify({"message": "Credentials not found. Use POST to create."}), 404

    data = request.json

    # Update only fields provided in request
    credentials.profession = data.get("profession", credentials.profession)
    credentials.YearsOfExperience = data.get("YearsOfExperience", credentials.YearsOfExperience)
    credentials.skills = data.get("skills", credentials.skills)
    credentials.description = data.get("description", credentials.description)
    credentials.businessInterests = data.get("businessInterests", credentials.businessInterests)

    db.session.commit()
    return jsonify({"message": "Credentials updated successfully"}), 200


@business_bp.route('/toggle-anonymous', methods=['POST'])
@jwt_required()
def toggle_anonymous():
    """
    Toggle anonymous mode for a business user
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
      - name: body
        in: body
        description: 'Optional username to set for anonymous profile'
        required: false
        schema:
          type: object
          properties:
            username:
              type: string
              example: "anon_user123"
    responses:
      200:
        description: Anonymous mode toggled successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Anonymous profile enabled"
            isAnonymous:
              type: boolean
              example: true
            anonymous:
              type: object
              properties:
                username:
                  type: string
                  example: "anon_user123"
      404:
        description: Business profile not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Business profile not found"
    """
    user_id = get_jwt_identity()
    business_info = BusinessBasicInfo.query.filter_by(user_id=user_id).first()

    if not business_info:
        return jsonify({"error": "Business profile not found"}), 404

    # Flip the state
    business_info.isAnonymous = not business_info.isAnonymous

    if business_info.isAnonymous:
        # Enable anonymous mode
        if not business_info.anonymousProfile:
            anon = BusinessAnonymous(username=request.json.get("username"))
            business_info.anonymousProfile = anon
            db.session.add(anon)
        else:
            if "username" in request.json:
                business_info.anonymousProfile.username = request.json["username"]

        message = "Anonymous profile enabled"
    else:
        # Disable anonymous mode
        message = "Anonymous profile disabled"

    db.session.commit()

    return jsonify({
        "message": message,
        "isAnonymous": business_info.isAnonymous,
        "anonymous": {
            "username": business_info.anonymousProfile.username if business_info.anonymousProfile else None
        }
    }), 200


@business_bp.route('/anonymous-status', methods=['GET'])
@jwt_required()
def get_anonymous_status():
    """
    Get anonymous mode status for a business user
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
        description: Current anonymous status
        schema:
          type: object
          properties:
            isAnonymous:
              type: boolean
              example: true
            anonymous:
              type: object
              properties:
                username:
                  type: string
                  example: "anon_user123"
      404:
        description: Business profile not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Business profile not found"
    """
    user_id = get_jwt_identity()
    business_info = BusinessBasicInfo.query.filter_by(user_id=user_id).first()

    if not business_info:
        return jsonify({"error": "Business profile not found"}), 404

    return jsonify({
        "isAnonymous": business_info.isAnonymous,
        "anonymous": {
            "username": business_info.anonymousProfile.username
            if business_info.anonymousProfile else None
        }
    }), 200


@business_bp.route('/edit-anonymous', methods=['PUT'])
@jwt_required()
def edit_anonymous():
    """
    Edit anonymous profile details for a business user
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
      - name: body
        in: body
        description: 'New details for the anonymous profile'
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "new_anon_username"
    responses:
      200:
        description: Anonymous profile updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Anonymous profile updated"
            anonymous:
              type: object
              properties:
                username:
                  type: string
                  example: "new_anon_username"
      404:
        description: Business or anonymous profile not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Anonymous profile not found"
    """
    user_id = get_jwt_identity()
    business_info = BusinessBasicInfo.query.filter_by(user_id=user_id).first()

    if not business_info or not business_info.anonymousProfile:
        return jsonify({"error": "Anonymous profile not found"}), 404

    data = request.json
    if "username" in data:
        business_info.anonymousProfile.username = data["username"]

    db.session.commit()

    return jsonify({
        "message": "Anonymous profile updated",
        "anonymous": {
            "username": business_info.anonymousProfile.username
        }
    }), 200


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
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer "
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
    current_user = User.query.get(current_user_id)
    print(current_user.account_type)

    if not current_user or not current_user.account_type:
        return jsonify({"error": "User does not belong to a valid account type"}), 403

    # Get distinct contact IDs
    sent_ids = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id)
    received_ids = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id)
    contact_ids = {row[0] for row in sent_ids.union(received_ids).distinct().all()}

    # Only include contacts of same account type
    contacts = User.query.filter(
        User.id.in_(contact_ids),
        User.account_type == current_user.account_type
    ).all()

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
    sender = User.query.get(sender_id)

    if not sender or not sender.account_type:
        return jsonify({"error": "Sender does not belong to a valid account type"}), 403

    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    # Enforce same account type
    if sender.account_type != receiver.account_type:
        return jsonify({"error": f"{sender.account_type.capitalize()} accounts can only message {sender.account_type.capitalize()} accounts"}), 403

    # Create and save message
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
    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)

    if not sender or not sender.account_type:
        return jsonify({"error": "Sender does not belong to a valid account type"}), 403

    if not receiver or not receiver.account_type:
        return jsonify({"error": "Receiver does not belong to a valid account type"}), 404

    # Enforce same account type
    if sender.account_type != receiver.account_type:
        return jsonify({
            "error": f"{sender.account_type.capitalize()} accounts "
                     f"can only view conversations with {sender.account_type.capitalize()} accounts"
        }), 403

    # Fetch conversation
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

"""
@business_bp.route('/api/photos', methods=['POST'])
@jwt_required()
def upload_photo():
    ""
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
    ""
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
    ""
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
    ""
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
"""