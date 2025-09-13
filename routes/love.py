from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv
)
from core.config import Config
from core.extensions import db
from core.models import User, LoveBasicInfo, UserPersonality, MatchPreference


love_bp = Blueprint('love', __name__)
load_dotenv()


@love_bp.route('/api/love/basic_info', methods=['POST'])
@jwt_required()
def set_basic_info():
    """
    User Basic Info Registration (First-Time Only)
    ---
    tags:
      - Love
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nickname
            - fullname
            - dateOfBirth
            - ageRange
            - maritalStatus
            - countryOfOrigin
            - tribe
            - currentLocation
            - skinTone
          properties:
            nickname:
              type: string
              example: JohnD
            fullname:
              type: string
              example: John Doe
            dateOfBirth:
              type: string
              format: date
              example: "1990-01-01"
            ageRange:
              type: string
              example: "25-35"
            maritalStatus:
              type: string
              example: Single
            countryOfOrigin:
              type: string
              example: USA
            tribe:
              type: string
              example: Apache
            currentLocation:
              type: string
              example: New York
            skinTone:
              type: string
              example: Brown
    responses:
      201:
        description: User info saved successfully
      400:
        description: Bad request
      404:
        description: User not found
      409:
        description: Info already exists. Update instead.
    """
    current_user_id = get_jwt_identity()
    data = request.json

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    required_fields = [
        "nickname", "fullname", "dateOfBirth", "ageRange", 
        "maritalStatus", "countryOfOrigin", "tribe", 
        "currentLocation", "skinTone"
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    try:
        dob = datetime.strptime(data["dateOfBirth"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "dateOfBirth must be in YYYY-MM-DD format"}), 400

    # Check if record exists
    existing_info = LoveBasicInfo.query.filter_by(user_id=current_user_id).first()
    if existing_info:
        return jsonify({"message": "Basic info already filled. Please update instead."}), 409

    # Create new record
    new_info = LoveBasicInfo(
        user_id=current_user_id,
        nickname=data["nickname"],
        fullname=data["fullname"],
        date_of_birth=dob,
        age_range=data["ageRange"],
        marital_status=data["maritalStatus"],
        country_of_origin=data["countryOfOrigin"],
        tribe=data["tribe"],
        current_location=data["currentLocation"],
        skin_tone=data["skinTone"]
    )
    db.session.add(new_info)

    user.account_type = "love"
    db.session.commit()

    return jsonify({"message": "User info saved successfully"}), 201


@love_bp.route('/api/love/basic_info', methods=['PUT'])
@jwt_required()
def update_basic_info():
    """
    Update User Basic Info
    ---
    tags:
      - Love
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - nickname
            - fullname
            - dateOfBirth
            - ageRange
            - maritalStatus
            - countryOfOrigin
            - tribe
            - currentLocation
            - skinTone
          properties:
            nickname:
              type: string
              example: JohnD
            fullname:
              type: string
              example: John Doe
            dateOfBirth:
              type: string
              format: date
              example: "1990-01-01"
            ageRange:
              type: string
              example: "25-35"
            maritalStatus:
              type: string
              example: Single
            countryOfOrigin:
              type: string
              example: USA
            tribe:
              type: string
              example: Apache
            currentLocation:
              type: string
              example: New York
            skinTone:
              type: string
              example: Brown
    responses:
      200:
        description: User info updated successfully
      400:
        description: Bad request
      404:
        description: User not found or no info to update
    """
    current_user_id = get_jwt_identity()
    data = request.json

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    required_fields = [
        "nickname", "fullname", "dateOfBirth", "ageRange", 
        "maritalStatus", "countryOfOrigin", "tribe", 
        "currentLocation", "skinTone"
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    try:
        dob = datetime.strptime(data["dateOfBirth"], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "dateOfBirth must be in YYYY-MM-DD format"}), 400

    # Check if info exists
    love_basic_info = LoveBasicInfo.query.filter_by(user_id=current_user_id).first()
    if not love_basic_info:
        return jsonify({"message": "No basic info found. Please set it first."}), 404

    # Update record
    love_basic_info.nickname = data["nickname"]
    love_basic_info.fullname = data["fullname"]
    love_basic_info.date_of_birth = dob
    love_basic_info.age_range = data["ageRange"]
    love_basic_info.marital_status = data["maritalStatus"]
    love_basic_info.country_of_origin = data["countryOfOrigin"]
    love_basic_info.tribe = data["tribe"]
    love_basic_info.current_location = data["currentLocation"]
    love_basic_info.skin_tone = data["skinTone"]

    db.session.commit()
    return jsonify({"message": "User info updated successfully"}), 200

    
@love_bp.route("/api/love/set_personality", methods=["POST"])
@jwt_required()
def set_love_personality():
    """
Set User Love Preferences
---
tags:
  - Love
security:
  - bearerAuth: []
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
        - height
        - eye_colour
        - body_type
        - hair_colour
        - hair_style
        - interest
        - hobbies
        - music
        - movies
        - activities
        - personality
        - religion
        - education
        - languages
        - values
      properties:
        height:
          type: string
          example: 180cm
        eye_colour:
          type: string
          example: Blue
        body_type:
          type: string
          example: Slim
        hair_colour:
          type: string
          example: Black
        hair_style:
          type: string
          example: Short
        interest:
          type: string
          example: Sports
        hobbies:
          type: string
          example: Reading, Travel
        music:
          type: string
          example: Rock
        movies:
          type: string
          example: Action
        activities:
          type: string
          example: Hiking
        personality:
          type: string
          example: Extrovert
        religion:
          type: string
          example: Christian
        education:
          type: string
          example: Bachelor
        languages:
          type: string
          example: English, French
        values:
          type: string
          example: Family-oriented
responses:
  201:
    description: Preferences saved successfully
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

    # Required fields
    required_fields = [
        "height", "eye_colour", "body_type", "hair_colour", "hair_style", 
        "interest", "hobbies", "music", "movies", "activities", 
        "personality", "religion", "education", "languages", "values"
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    # Check if personality already exists
    existing_personality = UserPersonality.query.filter_by(user_id=current_user_id).first()
    if existing_personality:
        return jsonify({
            "message": "Personality already filled. Please update instead."
        }), 409  # 409 Conflict

    # Create new personality record
    personality = UserPersonality(
        user_id=current_user_id,
        height=data["height"],
        eye_colour=data["eye_colour"],
        body_type=data["body_type"],
        hair_colour=data["hair_colour"],
        hair_style=data["hair_style"],
        interest=data["interest"],
        hobbies=data["hobbies"],
        music=data["music"],
        movies=data["movies"],
        activities=data["activities"],
        personality=data["personality"],
        religion=data["religion"],
        education=data["education"],
        languages=data["languages"],
        values=data["values"]
    )
    db.session.add(personality)
    db.session.commit()

    return jsonify({"message": "Personality set successfully"}), 201


@love_bp.route('/update-personality', methods=['PUT'])
@jwt_required()
def update_personality():
    """
    Update User Personality (partial update supported)
    ---
    tags:
      - Love
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            height:
              type: string
              example: "5'9"
            eye_colour:
              type: string
              example: "Brown"
            body_type:
              type: string
              example: "Athletic"
            hair_colour:
              type: string
              example: "Black"
            hair_style:
              type: string
              example: "Curly"
            interest:
              type: string
              example: "Technology, Arts"
            hobbies:
              type: string
              example: "Reading, Hiking"
            music:
              type: string
              example: "Jazz, Pop"
            movies:
              type: string
              example: "Action, Drama"
            activities:
              type: string
              example: "Travelling, Sports"
            personality:
              type: string
              example: "Extrovert"
            religion:
              type: string
              example: "Christian"
            education:
              type: string
              example: "Bachelor's Degree"
            languages:
              type: string
              example: "English, Spanish"
            values:
              type: string
              example: "Honesty, Integrity"
    responses:
      200:
        description: Personality updated successfully or no changes made
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Personality updated successfully"
      400:
        description: Invalid or missing JSON body
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Request body must be JSON"
      404:
        description: User not found or personality not set
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User not found"
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if data is None:
        return jsonify({"message": "Request body must be JSON"}), 400

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    existing_personality = UserPersonality.query.filter_by(user_id=current_user_id).first()
    if not existing_personality:
        return jsonify({
            "message": "No personality found. Please set it first."
        }), 404

    updated = False
    for field, value in data.items():
        if hasattr(existing_personality, field):
            setattr(existing_personality, field, value)
            updated = True

    if updated:
        db.session.commit()
        return jsonify({"message": "Personality updated successfully"}), 200
    else:
        return jsonify({"message": "No changes were made"}), 200


@love_bp.route("/api/love/match_preferences", methods=["POST"])
@jwt_required()
def set_match_preferences():
    """
    Set User Match Preferences (First-Time Only)
    ---
    tags:
      - Love
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - age_range
            - marital_status
            - country_of_origin
            - tribe
            - current_location
            - skin_tone
            - height
            - eye_colour
            - body_type
            - hair_colour
            - hair_style
            - religion
            - education
            - languages
            - values
            - interest
            - hobbies
            - music
            - movies
            - activities
            - personality
          properties:
            age_range:
              type: string
              example: "25-35"
            marital_status:
              type: string
              example: "Single"
            country_of_origin:
              type: string
              example: "Kenya"
            tribe:
              type: string
              example: "Kikuyu"
            current_location:
              type: string
              example: "Nairobi"
            skin_tone:
              type: string
              example: "Dark"
            height:
              type: string
              example: "170cm"
            eye_colour:
              type: string
              example: "Brown"
            body_type:
              type: string
              example: "Athletic"
            hair_colour:
              type: string
              example: "Black"
            hair_style:
              type: string
              example: "Curly"
            religion:
              type: string
              example: "Christian"
            education:
              type: string
              example: "Degree"
            languages:
              type: string
              example: "Swahili, English"
            values:
              type: string
              example: "Honesty"
            interest:
              type: string
              example: "Technology"
            hobbies:
              type: string
              example: "Hiking, Chess"
            music:
              type: string
              example: "Jazz"
            movies:
              type: string
              example: "Drama"
            activities:
              type: string
              example: "Yoga"
            personality:
              type: string
              example: "Introvert"
    responses:
      201:
        description: Match preferences saved successfully
      400:
        description: Bad request
      404:
        description: User not found
      409:
        description: Preferences already exist, update instead
    """
    current_user_id = get_jwt_identity()
    data = request.json

    # Verify user exists
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    required_fields = [
        "age_range", "marital_status", "country_of_origin", "tribe", "current_location",
        "skin_tone", "height", "eye_colour", "body_type", "hair_colour", "hair_style",
        "religion", "education", "languages", "values", "interest", "hobbies", "music",
        "movies", "activities", "personality"
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    existing_pref = MatchPreference.query.filter_by(user_id=current_user_id).first()
    if existing_pref:
        return jsonify({
            "message": "Match preferences already exist. Please update instead."
        }), 409

    # Create preferences
    new_pref = MatchPreference(user_id=current_user_id, **{field: data.get(field) for field in required_fields})
    db.session.add(new_pref)
    db.session.commit()

    return jsonify({"message": "Match preferences saved successfully"}), 201


@love_bp.route("/api/love/match_preferences", methods=["PUT"])
@jwt_required()
def update_match_preferences():
    """
    Update User Match Preferences (partial update supported)
    ---
    tags:
      - Love
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
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            age_range:
              type: string
              example: "25-35"
            marital_status:
              type: string
              example: "Single"
            country_of_origin:
              type: string
              example: "Kenya"
            tribe:
              type: string
              example: "Kikuyu"
            current_location:
              type: string
              example: "Nairobi"
            skin_tone:
              type: string
              example: "Dark"
            height:
              type: string
              example: "170cm"
            eye_colour:
              type: string
              example: "Brown"
            body_type:
              type: string
              example: "Athletic"
            hair_colour:
              type: string
              example: "Black"
            hair_style:
              type: string
              example: "Curly"
            religion:
              type: string
              example: "Christian"
            education:
              type: string
              example: "Degree"
            languages:
              type: string
              example: "Swahili, English"
            values:
              type: string
              example: "Honesty"
            interest:
              type: string
              example: "Technology"
            hobbies:
              type: string
              example: "Hiking, Chess"
            music:
              type: string
              example: "Jazz"
            movies:
              type: string
              example: "Drama"
            activities:
              type: string
              example: "Yoga"
            personality:
              type: string
              example: "Introvert"
    responses:
      200:
        description: Match preferences updated successfully or no changes made
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Match preferences updated successfully"
      400:
        description: Invalid or missing JSON body
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Request body must be JSON"
      404:
        description: User or preferences not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User not found"
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if data is None:
        return jsonify({"message": "Request body must be JSON"}), 400

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    existing_pref = MatchPreference.query.filter_by(user_id=current_user_id).first()
    if not existing_pref:
        return jsonify({"message": "No match preferences found. Please set them first."}), 404

    updated = False
    for field, value in data.items():
        if hasattr(existing_pref, field):
            setattr(existing_pref, field, value)
            updated = True

    if updated:
        db.session.commit()
        return jsonify({"message": "Match preferences updated successfully"}), 200
    else:
        return jsonify({"message": "No changes were made"}), 200
