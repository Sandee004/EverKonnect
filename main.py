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
from routes.love_routes import love_bp

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
    app.register_blueprint(love_bp)
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