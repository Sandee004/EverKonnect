from core.imports import (
    os, time, base64,
    Flask, request, jsonify,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv, threading,
    datetime, timedelta, date
)
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, oauth
from core.models import User, TempUser, UserPersonality, MatchPreference
from routes.auth_routes import auth_bp
from routes.love import love_bp
from routes.business import business_bp
from routes.connection import connection_bp
from routes.blog import blog_bp

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
    app.register_blueprint(business_bp)
    app.register_blueprint(connection_bp)
    app.register_blueprint(blog_bp)
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


@app.route('/api/referral', methods=['GET'])
@jwt_required()
def get_referral_code():
    """
    Get the current user's referral code
    ---
    tags:
      - Referral
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
        description: Referral code retrieved successfully
        schema:
          type: object
          properties:
            referral_code:
              type: string
              example: "X9T7ABCD"
            referral_points:
              type: integer
              example: 15
      404:
        description: User or referral code not found
        schema:
          type: object
          properties:
            message:
              type: string
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.referral_code:
        return jsonify({"message": "Referral code not found"}), 404

    return jsonify({
        "referral_code": user.referral_code,
        "referral_points": user.referral_points
    }), 200


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


def prepopulate_temp_users():
    users = [
        TempUser(email="test1@example.com", phone="+1234567890", otp_code="111111", otp_created_at=datetime.utcnow()),
        TempUser(email="test2@example.com", phone="+1987654321", otp_code="222222", otp_created_at=datetime.utcnow()),
        TempUser(email="test3@example.com", phone="+1122334455", otp_code="333333", otp_created_at=datetime.utcnow()),
    ]

    try:
        db.session.bulk_save_objects(users)
        db.session.commit()
        print("Temp users prepopulated successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"Error prepopulating temp users: {e}")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        prepopulate_temp_users()
    app.run(debug=True)