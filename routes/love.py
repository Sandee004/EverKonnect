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
def love_registration():
    """
User Basic Info Registration
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
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
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
    description: User not found
    """
    # Get user ID from JWT token
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

    # Check if LoveBasicInfo already exists
    love_basic_info = LoveBasicInfo.query.filter_by(user_id=current_user_id).first()

    if love_basic_info:
        # Update existing record
        love_basic_info.nickname = data["nickname"]
        love_basic_info.fullname = data["fullname"]
        love_basic_info.date_of_birth = dob
        love_basic_info.age_range = data["ageRange"]
        love_basic_info.marital_status = data["maritalStatus"]
        love_basic_info.country_of_origin = data["countryOfOrigin"]
        love_basic_info.tribe = data["tribe"]
        love_basic_info.current_location = data["currentLocation"]
        love_basic_info.skin_tone = data["skinTone"]
        message = "User info updated successfully"
    else:
        # Create new record
        love_basic_info = LoveBasicInfo(
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
        db.session.add(love_basic_info)
        message = "User info saved successfully"

    db.session.commit()
    return jsonify({"message": message}), 200


@love_bp.route("/api/love/account_type", methods=["POST"])
@jwt_required()
def set_account_type():
    """
    Set account type for the current user
    ---
    tags:
      - User
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: JWT token as Bearer <your_token>
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            accountType:
              type: string
              example: "love"  # or "business", etc.
    responses:
      200:
        description: Account type set successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Account type set successfully"
      404:
        description: User not found
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User not found"
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    account_type = data.get('accountType')

    if not account_type:
        return jsonify({"message": "Account type is required"}), 400

    user.account_type = account_type
    db.session.commit()

    return jsonify({"message": "Account type set successfully"}), 200

    
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
        
    height = data.get('height')
    eye_colour = data.get('eye_colour')
    body_type = data.get('body_type')
    hair_colour = data.get('hair_colour')
    hair_style = data.get('hair_style')
    interest = data.get('interest')
    hobbies = data.get('hobbies')
    music = data.get('music')
    movies = data.get('movies')
    activities = data.get('activities')
    personality = data.get('personality')
    religion = data.get('religion')
    education = data.get('education')
    languages = data.get('languages')
    values = data.get('values')

    required_fields = ["height", "eye_colour", "body_type", "hair_colour", "hair_style", "interest", "hobbies", "music", "movies", "activities", "personality", "religion", "education", "languages", "values"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    # Check if user already has personality set
    existing_personality = UserPersonality.query.filter_by(user_id=current_user_id).first()
    
    if existing_personality:
        # Update existing preferences
        for field in required_fields:
            setattr(existing_personality, field, data.get(field))
        message = "Personality updated successfully"
    else:
        # Create new preferences
        personality = UserPersonality(
            user_id=current_user_id,
            height=height,
            eye_colour=eye_colour,
            body_type=body_type,
            hair_colour=hair_colour,
            hair_style=hair_style,
            interest=interest,
            hobbies=hobbies,
            music=music,
            movies=movies,
            activities=activities,
            personality=personality,
            religion=religion,
            education=education,
            languages=languages,
            values=values
        )
        db.session.add(personality)
        message = "Personality saved successfully"

    db.session.commit()
    return jsonify({"message": message}), 200


@love_bp.route("/api/love/set_match_preferences", methods=["POST"])
@jwt_required()
def set_match_preferences():
    """
Set User Match Preferences
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
  200:
    description: Match preferences saved successfully
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
        "age_range", "marital_status", "country_of_origin", "tribe", "current_location",
        "skin_tone", "height", "eye_colour", "body_type", "hair_colour", "hair_style",
        "religion", "education", "languages", "values", "interest", "hobbies", "music",
        "movies", "activities", "personality"
    ]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    # Check if user already has match preferences
    existing_pref = MatchPreference.query.filter_by(user_id=current_user_id).first()

    if existing_pref:
        # Update existing preferences
        for field in required_fields:
            setattr(existing_pref, field, data.get(field))
        message = "Match preferences updated successfully"
    else:
        # Create new preferences
        new_pref = MatchPreference(
            user_id=current_user_id,
            age_range=data.get('age_range'),
            marital_status=data.get('marital_status'),
            country_of_origin=data.get('country_of_origin'),
            tribe=data.get('tribe'),
            current_location=data.get('current_location'),
            skin_tone=data.get('skin_tone'),
            height=data.get('height'),
            eye_colour=data.get('eye_colour'),
            body_type=data.get('body_type'),
            hair_colour=data.get('hair_colour'),
            hair_style=data.get('hair_style'),
            religion=data.get('religion'),
            education=data.get('education'),
            languages=data.get('languages'),
            values=data.get('values'),
            interest=data.get('interest'),
            hobbies=data.get('hobbies'),
            music=data.get('music'),
            movies=data.get('movies'),
            activities=data.get('activities'),
            personality=data.get('personality')
        )
        db.session.add(new_pref)
        message = "Match preferences saved successfully"

    db.session.commit()
    return jsonify({"message": message}), 200


