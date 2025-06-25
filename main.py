from core.imports import (
    os, time, base64,
    Flask, request, jsonify,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv, threading,
    datetime, timedelta, io, cv2, np, Image, date
)
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, oauth
from core.models import User, TempUser, UserPersonality, MatchPreference, LoveBasicInfo, BusinessBasicInfo, BusinessCredentials
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

    love_basic_info = user.love_basic_info
    if not love_basic_info:
        love_basic_info = LoveBasicInfo(
            user_id=user.id
        )

    # Fill the fields
    love_basic_info.nickname = nickname
    love_basic_info.fullname = fullname
    love_basic_info.date_of_birth = dob
    love_basic_info.age_range = ageRange
    love_basic_info.marital_status = maritalStatus
    love_basic_info.country_of_origin = countryOfOrigin
    love_basic_info.tribe = tribe
    love_basic_info.current_location = currentLocation
    love_basic_info.skin_tone = skinTone

    # Add if new record
    if not user.love_basic_info:
        db.session.add(love_basic_info)

    db.session.commit()
    return jsonify({"message": "User info updated successfully"}), 200


@app.route("/api/love/set_personality", methods=["POST"])
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
        # Update existing personalities
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


@app.route("/api/love/set_match_preferences", methods=["POST"])
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

###Business
@app.route('/api/business/basic_info', methods=['POST'])
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


@app.route("/api/business/add_credentials", methods=["POST"])
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