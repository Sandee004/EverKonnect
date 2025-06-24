from core.imports import (
    os, time, base64,
    Flask, request, jsonify,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv, threading,
    datetime, timedelta, io, cv2, np, Image, date
)
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, oauth
from core.models import User, TempUser, UserPersonality, MatchPreference
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    cors.init_app(app)
    bcrypt.init_app(app)
    oauth.init_app(app)

    app.register_blueprint(auth_bp)
    return app

app = create_app()

load_dotenv()


def cleanup_expired_temp_users():
    """Background function to clean expired temp users"""
    while True:
        try:
            with app.app_context():
                expiry_time = datetime.utcnow() - timedelta(hours=1)
                expired_users = TempUser.query.filter(TempUser.created_at < expiry_time).all()
                
                if expired_users:
                    for user in expired_users:
                        db.session.delete(user)
                    db.session.commit()
                    print(f"Cleaned up {len(expired_users)} expired temp users")
                
                # Sleep for 30 minutes before next cleanup
                time.sleep(3600)  # 1800 seconds = 30 minutes
        except Exception as e:
            print(f"Cleanup error: {e}")
            time.sleep(300)  # Wait 5 minutes on error

# Start cleanup thread when app starts
cleanup_thread = threading.Thread(target=cleanup_expired_temp_users, daemon=True)
cleanup_thread.start()


def model_to_dict(model):
    """Helper to convert a SQLAlchemy model to a dict."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def calculate_match_score(preferences, user, personality):
    score = 0
    current_location = db.Column(db.String(100), nullable=True)
    hair_style = db.Column(db.String(150), nullable=True)
    
    # 1. Exact matches for simple fields
    if preferences.age_range and preferences.age_range == user.age_range:
        score += 5

    if preferences.marital_status and preferences.marital_status == user.marital_status:
        score += 5
    if preferences.country_of_origin and preferences.country_of_origin == user.country_of_origin:
        score += 5
    if preferences.tribe and preferences.tribe == user.tribe:
        score += 5
    if preferences.skin_tone and preferences.skin_tone == user.skin_tone:
        score += 5
    if preferences.height and preferences.height == personality.height:
        score += 5
    if preferences.eye_colour and preferences.eye_colour == personality.eye_colour:
        score += 5
    if preferences.body_type and preferences.body_type == personality.body_type:
        score += 5
    if preferences.hair_colour and preferences.hair_colour == personality.hair_colour:
        score += 5
    if preferences.hair_style and preferences.hair_style == user.hair_style:
        score += 5
    if preferences.religion and preferences.religion == personality.religion:
        score += 5
    if preferences.education and preferences.education == personality.education:
        score += 5
    if preferences.languages and preferences.languages == personality.languages:
        score += 5

    # 3. Multi-value matches as lists
    def overlap_score(pref_string, user_string, weight):
        """Compare comma-separated lists and return partial weight based on overlap"""
        if not pref_string or not user_string:
            return 0
        pref_set = set([s.strip().lower() for s in pref_string.split(',') if s.strip()])
        user_set = set([s.strip().lower() for s in user_string.split(',') if s.strip()])
        overlap = pref_set & user_set
        if not pref_set:
            return 0
        return (len(overlap) / len(pref_set)) * weight

    # Interests, hobbies, movies, music, activities, values, personality
    score += overlap_score(preferences.interest, personality.interest, 5)
    score += overlap_score(preferences.hobbies, personality.hobbies, 5)
    score += overlap_score(preferences.movies, personality.movies, 5)
    score += overlap_score(preferences.music, personality.music, 5)
    score += overlap_score(preferences.activities, personality.activities, 5)
    score += overlap_score(preferences.values, personality.values, 5)
    score += overlap_score(preferences.personality, personality.personality, 5)

    return score  # Total up to 100

@app.route('/api/love/basic_info', methods=['POST'])
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

    # Find the current user
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get the fields
    nickname = data.get('nickname')
    fullname = data.get('fullname')
    dateOfBirth = data.get('dateOfBirth')
    ageRange = data.get('ageRange')
    maritalStatus = data.get('maritalStatus')
    countryOfOrigin = data.get('countryOfOrigin')
    tribe = data.get('tribe')
    currentLocation = data.get('currentLocation')
    skinTone = data.get('skinTone')

    required_fields = ["nickname", "fullname", "dateOfBirth", "ageRange", "maritalStatus", "countryOfOrigin", "tribe", "currentLocation", "skinTone"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    dob = None
    try:
        dob = datetime.strptime(dateOfBirth, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "dateOfBirth must be in YYYY-MM-DD format"}), 400

    # Update the user
    user.nickname = nickname
    user.fullname = fullname
    user.date_of_birth = dob
    user.age_range = ageRange
    user.marital_status = maritalStatus
    user.country_of_origin = countryOfOrigin
    user.tribe = tribe
    user.current_location = currentLocation
    user.skin_tone = skinTone

    db.session.commit()

    return jsonify({"message": "User info updated successfully"}), 200


@app.route("/api/love/set_preferences", methods=["POST"])
@jwt_required()
def set_love_preferences():
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

    # Check if user already has preferences
    existing_personality = UserPersonality.query.filter_by(user_id=current_user_id).first()
    
    if existing_personality:
        # Update existing preferences
        existing_personality.height = height
        existing_personality.eye_colour = eye_colour
        existing_personality.body_type = body_type
        existing_personality.hair_colour = hair_colour
        existing_personality.hair_style = hair_style
        existing_personality.interest = interest
        existing_personality.hobbies = hobbies
        existing_personality.music = music
        existing_personality.movies = movies
        existing_personality.activities = activities
        existing_personality.personality = personality
        existing_personality.religion = religion
        existing_personality.education = education
        existing_personality.languages = languages
        existing_personality.values = values
        message = "Preferences updated successfully"
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
        message = "Preferences saved successfully"

    db.session.commit()

    return jsonify({"message": message}), 200


@app.route('/matches', methods=['GET'])
@jwt_required()
def get_matches():
    """
    Get matches for the current logged-in user.

    This endpoint returns a list of potential matches for the current user
    based on their saved preferences.

    ---
    tags:
      - Matches
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
        description: A list of matches
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    type: integer
                    example: 123
                  nickname:
                    type: string
                    example: "JohnDoe"
                  score:
                    type: integer
                    example: 90
      400:
        description: Preferences not set
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()

    # Fetch current user and their preferences
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Get this user's preferences
    preferences = MatchPreference.query.filter_by(user_id=current_user_id).first()
    if not preferences:
        return jsonify({"message": "Preferences not set"}), 400

    # Get all other candidates
    candidates = User.query.filter(User.id != current_user_id).all()

    matches = []
    for candidate in candidates:
        personality = UserPersonality.query.filter_by(user_id=candidate.id).first()
        if not personality:
            continue

        # Compute score
        score = calculate_match_score(preferences, candidate, personality)

        if score >= 85:
            matches.append(
                {
                    "user_id": candidate.id,
                    "nickname": candidate.nickname,
                    "score": score
                }
            )

    # Sort matches by score descending
    matches.sort(key=lambda m: m['score'], reverse=True)

    return jsonify(matches), 200








@app.route('/show_temp_users')
def show_temp_users():
    users = TempUser.query.all()
    return jsonify([model_to_dict(user) for user in users])

@app.route('/show_users')
def show_users():
    users = User.query.all()
    return jsonify([model_to_dict(user) for user in users])


@app.route('/show_preferences')
def show_preferences():
    preferences = UserPersonality.query.all()
    return jsonify([model_to_dict(pref) for pref in preferences])


@app.route('/show_users_and_preferences')
def show_users_and_preferences():
    users = User.query.all()
    result = []
    for user in users:
        user_data = model_to_dict(user)
        # Add preference if it exists
        if user.preferences:
            user_data['preferences'] = model_to_dict(user.preferences)
        result.append(user_data)
    return jsonify(result)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)