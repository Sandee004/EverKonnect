from core.imports import (
    os, time, base64,
    Flask, request, jsonify,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv, threading,
    datetime, timedelta, date, filetype
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


@app.route('/ping')
def ping():
    return "Pong", 200

def model_to_dict(model):
    """Helper to convert a SQLAlchemy model to a dict."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}


def calculate_match_score(preferences, user, personality):
    score = 0

    # 1. Exact matches for simple fields
    if preferences.age_range and preferences.age_range == user.love_basic_info.age_range:
        score += 5
    if preferences.marital_status and preferences.marital_status == user.love_basic_info.marital_status:
        score += 5
    if preferences.country_of_origin and preferences.country_of_origin == user.love_basic_info.country_of_origin:
        score += 5
    if preferences.tribe and preferences.tribe == user.love_basic_info.tribe:
        score += 5
    if preferences.skin_tone and preferences.skin_tone == user.love_basic_info.skin_tone:
        score += 5

    if preferences.height and preferences.height == personality.height:
        score += 5
    if preferences.eye_colour and preferences.eye_colour == personality.eye_colour:
        score += 5
    if preferences.body_type and preferences.body_type == personality.body_type:
        score += 5
    if preferences.hair_colour and preferences.hair_colour == personality.hair_colour:
        score += 5
    if preferences.hair_style and preferences.hair_style == personality.hair_style:
        score += 5
    if preferences.religion and preferences.religion == personality.religion:
        score += 5
    if preferences.education and preferences.education == personality.education:
        score += 5
    if preferences.languages and preferences.languages == personality.languages:
        score += 5

    # 2. Multi-value list fields
    def overlap_score(pref_string, user_string, weight):
        """Compare comma-separated lists and return partial weight based on overlap"""
        if not pref_string or not user_string:
            return 0
        pref_set = {s.strip().lower() for s in pref_string.split(',') if s.strip()}
        user_set = {s.strip().lower() for s in user_string.split(',') if s.strip()}
        overlap = pref_set & user_set
        if not pref_set:
            return 0
        return (len(overlap) / len(pref_set)) * weight

    # Compare interests, hobbies, etc.
    score += overlap_score(preferences.interest, personality.interest, 5)
    score += overlap_score(preferences.hobbies, personality.hobbies, 5)
    score += overlap_score(preferences.movies, personality.movies, 5)
    score += overlap_score(preferences.music, personality.music, 5)
    score += overlap_score(preferences.activities, personality.activities, 5)
    score += overlap_score(preferences.values, personality.values, 5)
    score += overlap_score(preferences.personality, personality.personality, 5)

    return score  # Total max: 100


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
                  profile_pic:
                    type: string
                    example: "data:image/jpeg;base64,..."
      400:
        description: Preferences not set
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    preferences = MatchPreference.query.filter_by(user_id=current_user_id).first()
    if not preferences:
        return jsonify({"message": "Preferences not set"}), 400

    candidates = User.query.filter(
        User.id != current_user_id,
        User.account_type == user.account_type
    ).all()

    matches = []
    for candidate in candidates:
        if not candidate.love_basic_info or not candidate.personality:
            continue

        score = calculate_match_score(preferences, candidate, candidate.personality)
        if score < 85:
            continue

        # Prepare profile picture
        profile_pic_data = None
        if candidate.profile_pic:
            try:
                image_bytes = base64.b64decode(candidate.profile_pic)
                kind = filetype.guess(image_bytes)
                extension = kind.extension if kind else "jpeg"
                mime_type = f"image/{extension}" if extension in ['jpeg', 'png'] else "image/jpeg"
                profile_pic_data = f"data:{mime_type};base64,{candidate.profile_pic}"
            except Exception:
                profile_pic_data = None

        matches.append({
            "user_id": candidate.id,
            "nickname": candidate.love_basic_info.nickname,
            "score": int(score),
            "profile_pic": profile_pic_data
        })

    matches.sort(key=lambda m: m['score'], reverse=True)

    return jsonify(matches), 200


@app.route('/match/account/<int:user_id>', methods=['GET'])
@jwt_required()
def get_match_account(user_id):
    """
    Get full profile details for a selected match by user ID.

    ---
    tags:
      - Matches
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        description: ID of the user to retrieve
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Full profile of the selected match
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                email:
                  type: string
                phone:
                  type: string
                profile_pic:
                  type: string
                nickname:
                  type: string
                fullname:
                  type: string
                date_of_birth:
                  type: string
                age_range:
                  type: string
                marital_status:
                  type: string
                country_of_origin:
                  type: string
                tribe:
                  type: string
                current_location:
                  type: string
                skin_tone:
                  type: string
                personality:
                  type: object
      404:
        description: User not found
    """
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    love_info = user.love_basic_info
    personality = user.personality

    # Process profile picture
    profile_pic_data = None
    if user.profile_pic:
        try:
            image_bytes = base64.b64decode(user.profile_pic)
            kind = filetype.guess(image_bytes)
            extension = kind.extension if kind else "jpeg"
            mime_type = f"image/{extension}" if extension in ["jpeg", "png"] else "image/jpeg"
            profile_pic_data = f"data:{mime_type};base64,{user.profile_pic}"
        except Exception:
            profile_pic_data = None

    user_data = {
        "user_id": user.id,
        "email": user.email,
        "phone": user.phone,
        "profile_pic": profile_pic_data,
        "nickname": love_info.nickname if love_info else None,
        "fullname": love_info.fullname if love_info else None,
        "date_of_birth": love_info.date_of_birth.isoformat() if love_info and love_info.date_of_birth else None,
        "age_range": love_info.age_range if love_info else None,
        "marital_status": love_info.marital_status if love_info else None,
        "country_of_origin": love_info.country_of_origin if love_info else None,
        "tribe": love_info.tribe if love_info else None,
        "current_location": love_info.current_location if love_info else None,
        "skin_tone": love_info.skin_tone if love_info else None,
        "personality": {
            "height": personality.height if personality else None,
            "eye_colour": personality.eye_colour if personality else None,
            "body_type": personality.body_type if personality else None,
            "hair_colour": personality.hair_colour if personality else None,
            "hair_style": personality.hair_style if personality else None,
            "interest": personality.interest if personality else None,
            "hobbies": personality.hobbies if personality else None,
            "music": personality.music if personality else None,
            "movies": personality.movies if personality else None,
            "activities": personality.activities if personality else None,
            "personality": personality.personality if personality else None,
            "religion": personality.religion if personality else None,
            "education": personality.education if personality else None,
            "languages": personality.languages if personality else None,
            "values": personality.values if personality else None
        }
    }

    return jsonify(user_data), 200


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
    # Prevent duplicate inserts
    if TempUser.query.first():
        print("Temp users already exist. Skipping prepopulation.")
        return

    users = [
        TempUser(
            email="test1@example.com",
            phone="+1234567890",
            otp_code="111111",
            otp_created_at=datetime.utcnow()
        ),
        TempUser(
            email="test2@example.com",
            phone="+1987654321",
            otp_code="222222",
            otp_created_at=datetime.utcnow()
        ),
        TempUser(
            email="test3@example.com",
            phone="+1122334455",
            otp_code="333333",
            otp_created_at=datetime.utcnow()
        ),
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