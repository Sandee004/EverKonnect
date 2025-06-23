from core.imports import (
    os, time, json, hmac, base64, requests,
    Flask, request, jsonify, render_template, redirect, Mail, Message,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    Swagger, load_dotenv, threading,
    datetime, timedelta, io, cv2, np, Image
)
from core.config import Config
from core.extensions import db, jwt, mail, swagger, cors
from core.models import User, TempUser, Preference
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    swagger.init_app(app)
    cors.init_app(app)

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


@app.route('/api/love/basic_info', methods=['POST'])
@jwt_required()
def love_registration():
    """
    User Basic Info Registration
    ---
    tags:
      - Love
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
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
    existing_preference = Preference.query.filter_by(user_id=current_user_id).first()
    
    if existing_preference:
        # Update existing preferences
        existing_preference.height = height
        existing_preference.eye_colour = eye_colour
        existing_preference.body_type = body_type
        existing_preference.hair_colour = hair_colour
        existing_preference.hair_style = hair_style
        existing_preference.interest = interest
        existing_preference.hobbies = hobbies
        existing_preference.music = music
        existing_preference.movies = movies
        existing_preference.activities = activities
        existing_preference.personality = personality
        existing_preference.religion = religion
        existing_preference.education = education
        existing_preference.languages = languages
        existing_preference.values = values
        message = "Preferences updated successfully"
    else:
        # Create new preferences
        preference = Preference(
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
        db.session.add(preference)
        message = "Preferences saved successfully"

    db.session.commit()

    return jsonify({"message": message}), 200


@app.route('/show_users')
def show_users():
    users = User.query.all()
    return jsonify([model_to_dict(user) for user in users])


@app.route('/api/verify-face', methods=['POST'])
def verify_face():
    """
    Verify that the provided image contains at least one face
    ---
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            face_image:
              type: string
              description: Base64-encoded face image
              example: "<Base64 string>"
    responses:
      200:
        description: Face detected successfully
      400:
        description: No face detected or bad image
    """

    data = request.get_json()
    face_image_b64 = data.get('face_image')
    if not face_image_b64:
        return jsonify({"error": "face_image is required"}), 400

    try:
        # Decode the base64 image
        image_data = base64.b64decode(face_image_b64)
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        image_np = np.array(image)

        # Load OpenCV's built-in face detector
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        if len(faces) == 0:
            return jsonify({"error": "No face detected"}), 400
        else:
            return jsonify({"message": f"{len(faces)} face(s) detected"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 400


@app.route('/show_preferences')
def show_preferences():
    preferences = Preference.query.all()
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