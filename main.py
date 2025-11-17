from core.imports import ( base64,
    Flask, request, jsonify,
    JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv,
    datetime, timedelta, date, filetype, IntegrityError, SocketIO, emit
)
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors, bcrypt, oauth
from core.models import User, TempUser, UserPersonality, MatchPreference, SavedPhoto, LoveBasicInfo, BusinessBasicInfo, BusinessCredentials
from routes.auth_routes import auth_bp
from routes.love import love_bp
from routes.business import business_bp
from routes.connection import connection_bp
from routes.blog import blog_bp
from routes.gallery import gallery_bp
from routes.calls import call_bp
load_dotenv()

socketio = SocketIO(cors_allowed_origins="*")

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
    socketio.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(love_bp)
    app.register_blueprint(business_bp)
    app.register_blueprint(connection_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(call_bp)
    return app

app = create_app()

@app.route('/ping')
def ping():
    return "Pong", 200

def model_to_dict(model):
    """Helper to convert a SQLAlchemy model to a dict."""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}

def seed_love_users():
    """Prepopulate the database with 5 users and their related info, including preferences."""
    users_data = [
        {
            "email": "alice@example.com",
            "phone": "1234567890",
            "username": "alice123",
            "account_type": "love",
            "love_basic_info": {
                "nickname": "Alice",
                "fullname": "Alice Johnson",
                "date_of_birth": date(1995, 5, 20),
                "age_range": "25-30",
                "marital_status": "Single",
                "country_of_origin": "USA",
                "tribe": "Navajo",
                "current_location": "New York",
                "skin_tone": "Fair"
            },
            "personality": {
                "height": "5'6",
                "eye_colour": "Blue",
                "body_type": "Slim",
                "hair_colour": "Blonde",
                "hair_style": "Straight",
                "interest": "travel, cooking, reading",
                "hobbies": "yoga, hiking",
                "music": "pop, jazz",
                "movies": "romance, drama",
                "activities": "dancing, volunteering",
                "personality": "extrovert, kind",
                "religion": "Christianity",
                "education": "Bachelor's",
                "languages": "English, Spanish",
                "values": "family, honesty"
            },
            "matchpreference": {
                "age_range": "27-35",
                "marital_status": "Single",
                "country_of_origin": "USA",
                "current_location": "USA",
                "body_type": "Athletic",
                "religion": "Christianity",
                "education": "Bachelor's or higher",
                "languages": "English",
                "values": "family, honesty, ambition"
            }
        },
        {
            "email": "bob@example.com",
            "phone": "9876543210",
            "username": "bobster",
            "account_type": "love",
            "love_basic_info": {
                "nickname": "Bob",
                "fullname": "Bob Williams",
                "date_of_birth": date(1990, 8, 10),
                "age_range": "30-35",
                "marital_status": "Single",
                "country_of_origin": "Canada",
                "tribe": "Cree",
                "current_location": "Toronto",
                "skin_tone": "Medium"
            },
            "personality": {
                "height": "5'10",
                "eye_colour": "Brown",
                "body_type": "Athletic",
                "hair_colour": "Black",
                "hair_style": "Curly",
                "interest": "sports, travel, photography",
                "hobbies": "cycling, basketball",
                "music": "rock, hip-hop",
                "movies": "action, comedy",
                "activities": "gym, concerts",
                "personality": "adventurous, funny",
                "religion": "Islam",
                "education": "Master's",
                "languages": "English, French",
                "values": "loyalty, ambition"
            },
            "matchpreference": {
                "age_range": "25-32",
                "marital_status": "Single",
                "country_of_origin": "Canada",
                "current_location": "Toronto",
                "body_type": "Slim or Athletic",
                "religion": "Islam",
                "education": "Bachelor's or higher",
                "languages": "English, French",
                "values": "loyalty, family"
            }
        },
        {
            "email": "charlie@example.com",
            "phone": "5551112222",
            "username": "charlie_x",
            "account_type": "love",
            "love_basic_info": {
                "nickname": "Charlie",
                "fullname": "Charlie Kim",
                "date_of_birth": date(1993, 3, 15),
                "age_range": "25-30",
                "marital_status": "Divorced",
                "country_of_origin": "South Korea",
                "tribe": "None",
                "current_location": "Seoul",
                "skin_tone": "Light"
            },
            "personality": {
                "height": "5'8",
                "eye_colour": "Black",
                "body_type": "Average",
                "hair_colour": "Brown",
                "hair_style": "Wavy",
                "interest": "gaming, anime, technology",
                "hobbies": "coding, chess",
                "music": "kpop, edm",
                "movies": "sci-fi, thriller",
                "activities": "esports, hiking",
                "personality": "introvert, thoughtful",
                "religion": "Buddhism",
                "education": "Bachelor's",
                "languages": "Korean, English",
                "values": "respect, discipline"
            },
            "matchpreference": {
                "age_range": "23-29",
                "marital_status": "Single or Divorced",
                "country_of_origin": "South Korea",
                "current_location": "Seoul",
                "body_type": "Slim or Average",
                "religion": "Buddhism or None",
                "education": "Any",
                "languages": "Korean, English",
                "values": "kindness, respect"
            }
        },
        {
            "email": "diana@example.com",
            "phone": "4449998888",
            "username": "diana_queen",
            "account_type": "love",
            "love_basic_info": {
                "nickname": "Diana",
                "fullname": "Diana Prince",
                "date_of_birth": date(1998, 11, 25),
                "age_range": "20-25",
                "marital_status": "Single",
                "country_of_origin": "UK",
                "tribe": "None",
                "current_location": "London",
                "skin_tone": "Olive"
            },
            "personality": {
                "height": "5'7",
                "eye_colour": "Green",
                "body_type": "Slim",
                "hair_colour": "Red",
                "hair_style": "Straight",
                "interest": "fashion, arts, travel",
                "hobbies": "painting, blogging",
                "music": "indie, pop",
                "movies": "romantic comedy, fantasy",
                "activities": "museum visits, cooking",
                "personality": "creative, caring",
                "religion": "Christianity",
                "education": "Bachelor's",
                "languages": "English, Italian",
                "values": "kindness, creativity"
            },
            "matchpreference": {
                "age_range": "25-32",
                "marital_status": "Single",
                "country_of_origin": "UK or Europe",
                "current_location": "London",
                "body_type": "Athletic or Slim",
                "religion": "Christianity",
                "education": "Bachelor's or higher",
                "languages": "English",
                "values": "creativity, kindness"
            }
        },
        {
            "email": "eric@example.com",
            "phone": "2227776666",
            "username": "eric_the_great",
            "account_type": "love",
            "love_basic_info": {
                "nickname": "Eric",
                "fullname": "Eric Johnson",
                "date_of_birth": date(1992, 6, 5),
                "age_range": "30-35",
                "marital_status": "Single",
                "country_of_origin": "USA",
                "tribe": "Cherokee",
                "current_location": "Los Angeles",
                "skin_tone": "Dark"
            },
            "personality": {
                "height": "6'0",
                "eye_colour": "Hazel",
                "body_type": "Muscular",
                "hair_colour": "Black",
                "hair_style": "Buzzcut",
                "interest": "fitness, business, travel",
                "hobbies": "gym, investing",
                "music": "hip-hop, r&b",
                "movies": "thriller, documentary",
                "activities": "networking, basketball",
                "personality": "confident, driven",
                "religion": "Atheist",
                "education": "MBA",
                "languages": "English, Spanish",
                "values": "success, honesty"
            },
            "matchpreference": {
                "age_range": "25-32",
                "marital_status": "Single",
                "country_of_origin": "USA",
                "current_location": "Los Angeles",
                "body_type": "Slim or Athletic",
                "religion": "Any",
                "education": "Bachelor's or higher",
                "languages": "English",
                "values": "confidence, honesty"
            }
        },
    ]

    raw_password = "password123"
    hashed_password = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    created_count = 0
    for data in users_data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing:
            print(f"⚠️ User with email {data['email']} already exists, skipping.")
            continue

        user = User(
            email=data["email"],
            phone=data["phone"],
            username=data["username"],
            password_hash=hashed_password,
            account_type=data["account_type"]
        )
        db.session.add(user)
        db.session.flush()  # ensures user.id is available

        love_info = LoveBasicInfo(user_id=user.id, **data["love_basic_info"])
        personality = UserPersonality(user_id=user.id, **data["personality"])
        preference = MatchPreference(user_id=user.id, **data["matchpreference"])

        db.session.add(love_info)
        db.session.add(personality)
        db.session.add(preference)

        created_count += 1

    try:
        db.session.commit()
        print(f"✅ {created_count} new users seeded successfully (all with password123)!")
    except IntegrityError:
        db.session.rollback()
        print("❌ Seeding failed due to duplicate unique fields.")


def seed_business_users():
    """Prepopulate the database with 3 business accounts and their related info."""
    business_users_data = [
        {
            "email": "coffeehub@example.com",
            "phone": "1112223333",
            "username": "coffeehub",
            "account_type": "business",
            "business_basic_info": {
                "fullname": "James Smith",
                "homeAddress": "123 Main St",
                "phone": "1112223333",
                "country": "USA",
                "state": "New York",
                "city": "New York",
                "language": "English, Spanish",
                "sex": "Male",
                "DoB": "1985-04-12",
                "businessName": "Coffee Hub",
                "businessAddress": "123 Coffee St, New York, NY"
            },
            "business_credentials": {
                "profession": "Cafe Owner",
                "YearsOfExperience": 10,
                "skills": "Customer service, coffee brewing, management",
                "description": "Runs a modern coffee shop serving artisan coffee and pastries.",
                "businessInterests": "Expanding franchise, coffee culture, community events"
            }
        },
        {
            "email": "techflow@example.com",
            "phone": "2223334444",
            "username": "techflow",
            "account_type": "business",
            "business_basic_info": {
                "fullname": "Sophia Chen",
                "homeAddress": "456 Silicon Ave",
                "phone": "2223334444",
                "country": "USA",
                "state": "California",
                "city": "San Francisco",
                "language": "English, Mandarin",
                "sex": "Female",
                "DoB": "1990-07-08",
                "businessName": "TechFlow Solutions",
                "businessAddress": "789 Startup Rd, San Francisco, CA"
            },
            "business_credentials": {
                "profession": "Software Engineer / CEO",
                "YearsOfExperience": 8,
                "skills": "Python, Cloud computing, Leadership",
                "description": "Founder of a SaaS company providing cloud-based productivity tools.",
                "businessInterests": "AI, SaaS, cloud technology, startups"
            }
        },
        {
            "email": "fitlife@example.com",
            "phone": "3334445555",
            "username": "fitlife",
            "account_type": "business",
            "business_basic_info": {
                "fullname": "Michael Johnson",
                "homeAddress": "789 Fitness Blvd",
                "phone": "3334445555",
                "country": "USA",
                "state": "Illinois",
                "city": "Chicago",
                "language": "English",
                "sex": "Male",
                "DoB": "1988-11-22",
                "businessName": "FitLife Gym",
                "businessAddress": "456 Health St, Chicago, IL"
            },
            "business_credentials": {
                "profession": "Fitness Trainer / Gym Owner",
                "YearsOfExperience": 12,
                "skills": "Personal training, business management, nutrition",
                "description": "Owns a premium fitness center with modern equipment and personal training.",
                "businessInterests": "Health, fitness, wellness coaching"
            }
        },
    ]

    raw_password = "password123"
    hashed_password = bcrypt.generate_password_hash(raw_password).decode('utf-8')

    created_count = 0
    for data in business_users_data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing:
            print(f"⚠️ Business user with email {data['email']} already exists, skipping.")
            continue

        user = User(
            email=data["email"],
            phone=data["phone"],
            username=data["username"],
            password_hash=hashed_password,
            account_type=data["account_type"]
        )
        db.session.add(user)
        db.session.flush()  # ensures user.id is available

        business_info = BusinessBasicInfo(user_id=user.id, **data["business_basic_info"])
        credentials = BusinessCredentials(user_id=user.id, **data["business_credentials"])

        db.session.add(business_info)
        db.session.add(credentials)

        created_count += 1

    try:
        db.session.commit()
        print(f"✅ {created_count} new business users seeded successfully (all with password123)!")
    except IntegrityError:
        db.session.rollback()
        print("❌ Seeding business users failed due to duplicate unique fields.")


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

    # Sort so highest score is first
    matches.sort(key=lambda m: m['score'], reverse=True)

    return jsonify(matches), 200


@app.route('/match/account/<int:user_id>', methods=['GET'])
@jwt_required()
def get_match_account(user_id):
    """
    Get full profile details for a selected match by user ID, including profile picture and gallery photos.

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
                  description: Base64-encoded profile picture (with MIME type prefix) or null
                gallery_photos:
                  type: array
                  items:
                    type: string
                  description: List of Cloudinary image URLs from the user's gallery
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
                  properties:
                    height:
                      type: string
                    eye_colour:
                      type: string
                    body_type:
                      type: string
                    hair_colour:
                      type: string
                    hair_style:
                      type: string
                    interest:
                      type: string
                    hobbies:
                      type: string
                    music:
                      type: string
                    movies:
                      type: string
                    activities:
                      type: string
                    personality:
                      type: string
                    religion:
                      type: string
                    education:
                      type: string
                    languages:
                      type: string
                    values:
                      type: string
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

    saved_photos = SavedPhoto.query.filter_by(user_id=user_id).order_by(SavedPhoto.uploaded_at.desc()).all()
    gallery_photos = [photo.photo_url for photo in saved_photos]

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
        },
        "gallery_photos": gallery_photos
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
    """
    Get all users
    ---
    tags:
      - User
    summary: Retrieve all users
    responses:
      200:
        description: List of users
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
    """
    users = User.query.all()
    return jsonify([model_to_dict(user) for user in users])

@app.route('/show_love_users')
def show_love_users():
    """
    Get all users with LoveBasicInfo
    ---
    tags:
      - User
    summary: Retrieve all users that have love profile info
    responses:
      200:
        description: List of users with love_basic_info
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
    """
    #users = User.query.filter(User.love_basic_info.isnot(None)).all()
    users = User.query.filter(User.account_type == "love").all()
    return jsonify([model_to_dict(user) for user in users])

@app.route('/show_business_users')
def show_business_users():
    """
    Get all users with BusinessBasicInfo
    ---
    tags:
      - User
    summary: Retrieve all users that have business profile info
    responses:
      200:
        description: List of users with business_basic_info
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
    """
    #users = User.query.filter(User.business_basic_info.isnot(None)).all()
    users = User.query.filter(User.account_type == " business").all()
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
        try:
            prepopulate_temp_users()
            seed_love_users()
            seed_business_users()
        except Exception as e:
            print(f"⚠️ Seed error: {e}")

    socketio.run(app, host="0.0.0.0", port=5000, debug=True)