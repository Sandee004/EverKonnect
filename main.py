from twilio.rest import Client
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
from datetime import timedelta, datetime
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flasgger import Swagger
from datetime import datetime, timedelta
import random
import os
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///everkonnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

jwt = JWTManager(app)
db = SQLAlchemy(app)
mail = Mail(app)
bcrypt = Bcrypt(app)
swagger = Swagger(app)

CORS(app)

MAIL_SERVER = 'smtp.zoho.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.getenv("USERNAME_FOR_EMAIL")
MAIL_PASSWORD = os.getenv("PASSWORD_FOR_EMAIL")
MAIL_DEFAULT_SENDER = os.getenv("USERNAME_FOR_EMAIL")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    nickname = db.Column(db.String(100), nullable=True)
    fullname = db.Column(db.String(150), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    age_range = db.Column(db.String(50), nullable=True)
    marital_status = db.Column(db.String(50), nullable=True)
    country_of_origin = db.Column(db.String(100), nullable=True)
    tribe = db.Column(db.String(100), nullable=True)
    current_location = db.Column(db.String(100), nullable=True)
    skin_tone = db.Column(db.String(50), nullable=True)

    preferences = db.relationship('Preference', backref='user', uselist=False)


class Preference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    height = db.Column(db.String(150), nullable=True)
    eye_colour = db.Column(db.String(150), nullable=True)
    body_type = db.Column(db.String(150), nullable=True)
    hair_colour = db.Column(db.String(150), nullable=True)
    hair_style = db.Column(db.String(150), nullable=True)
    interest = db.Column(db.String(150), nullable=True)
    hobbies = db.Column(db.String(150), nullable=True)
    music = db.Column(db.String(150), nullable=True)
    movies = db.Column(db.String(150), nullable=True)
    activities = db.Column(db.String(150), nullable=True)
    personality = db.Column(db.String(150), nullable=True)
    religion = db.Column(db.String(150), nullable=True)
    education = db.Column(db.String(150), nullable=True)
    languages = db.Column(db.String(150), nullable=True)
    values = db.Column(db.String(150), nullable=True)

def send_email_otp(to, subject, body):
    msg = Message(subject=subject,
                  recipients=[to])
    msg.html = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def send_sms_otp(phone, otp):
    account_sid = "your_twilio_sid"
    auth_token = "your_twilio_auth_token"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=f"Your verification code is {otp}.",
        from_="+1234567890",  # your Twilio number
        to=phone
    )

@app.route('/api/auth', methods=["POST"])
def auth():
    """
    Request OTP for authentication
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
            phone:
              type: string
              example: "+1234567890"
    responses:
      200:
        description: OTP sent successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OTP sent to user@example.com"
      400:
        description: Bad Request
        schema:
          type: object
          properties:
            error:
              type: string
    """
    email = request.json.get('email')
    phone = request.json.get('phone')

    if not email and not phone:
        return jsonify({"error": "Email or phone is required"}), 400

    # Find existing user or create a new one
    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone:
        user = User.query.filter_by(phone=phone).first()

    if not user:
        user = User(email=email, phone=phone)
        db.session.add(user)

    otp = str(random.randint(100000, 999999))
    user.otp_code = otp
    user.otp_created_at = datetime.utcnow()
    db.session.commit()

  
    if email:
        subject = "Your verification code"
        body = f"<p>Your verification code is <strong>{otp}</strong></p>"
        send_email_otp(email, subject, body)
        return jsonify({"message": f"OTP sent to {email}"}), 200
    elif phone:
        send_sms_otp(phone, otp)
        return jsonify({"message": f"OTP sent to {phone}"}), 200


@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """
    Verify OTP
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            email:
              type: string
            phone:
              type: string
            otp:
              type: string
    responses:
      200:
        description: OTP verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OTP verified successfully"
      400:
        description: Bad request (invalid or expired OTP)
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    email = request.json.get('email')
    phone = request.json.get('phone')
    otp = request.json.get('otp')

    if not otp or (not email and not phone):
        return jsonify({"error": "OTP and email or phone is required"}), 400

    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone:
        user = User.query.filter_by(phone=phone).first()

    if not user:
        return jsonify({"error": "User not found"}), 404


    expiry_time = user.otp_created_at + timedelta(minutes=5)
    if user.otp_code != otp:
        return jsonify({"error": "Invalid OTP"}), 400
    elif datetime.utcnow() > expiry_time:
        return jsonify({"error": "OTP expired"}), 400

    
    user.otp_code = None
    user.otp_created_at = None
    db.session.commit()

    return jsonify({"message": "OTP verified successfully"}), 200


@app.route('/api/set-credentials', methods=['POST'])
def set_credentials():
    """
    Set user credentials (username and password)
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              example: "user@example.com"
            phone:
              type: string
              example: "+1234567890"
            username:
              type: string
              example: "new_user"
            password:
              type: string
              format: password
              example: "Str0ngP@ssword!"
    responses:
      200:
        description: Credentials saved successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Credentials saved successfully"
      400:
        description: Missing or invalid parameters
        schema:
          type: object
          properties:
            error:
              type: string
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
    """
    email = request.json.get('email')
    phone = request.json.get('phone')
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password or (not email and not phone):
        return jsonify({"error": "username, password, and email or phone are required"}), 400

    user = None
    if email:
        user = User.query.filter_by(email=email).first()
    elif phone:
        user = User.query.filter_by(phone=phone).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user.id:
        return jsonify({"error": "Username already exists"}), 400

    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    user.username = username
    user.password_hash = password_hash
    db.session.commit()

    return jsonify({"message": "Credentials saved successfully"}), 200


@app.route('/api/love/basic_info', methods=['POST'])
def love_registration():
    """
    User Basic Info Registration
    ---
    tags:
      - Love
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
      201:
        description: User created successfully
      400:
        description: Bad request
    """
    data = request.json

    nickname = data.get('email')
    fullname = data.get('phone')
    dateOfBirth = data.get('username')
    ageRange = data.get('password')
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

    # Create and save the User
    user = User(
        nickname=nickname,
        fullname=fullname,
        date_of_birth=dob,
        age_range=ageRange,
        marital_status=maritalStatus,
        country_of_origin=countryOfOrigin,
        tribe=tribe,
        current_location=currentLocation,
        skin_tone=skinTone,
    )
    db.session.add(user)
    db.session.commit()

@app.route("/api/love/set_preferences", methods=["POST"])
def set_love_preferences():
    """
    Set User Love Preferences
    ---
    tags:
      - Love
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
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
            user_id:
              type: integer
              example: 1
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
    """
    data = request.json
    user_id=data.get("user_id")

    if not user_id:
        return jsonify({"message": "user_id is required"}), 400
        

    height=data.get('height'),
    eye_colour=data.get('eye_colour'),
    body_type=data.get('body_type'),
    hair_colour=data.get('hair_colour'),
    hair_style=data.get('hair_style'),
    interest=data.get('interest'),
    hobbies=data.get('hobbies'),
    music=data.get('music'),
    movies=data.get('movies'),
    activities=data.get('activities'),
    personality=data.get('personality'),
    religion=data.get('religion'),
    education=data.get('education'),
    languages=data.get('languages'),
    values=data.get('values')

    required_fields = ["height", "eye_colour", "body_type", "hair_colour", "hair_style", "interest", "hobbies", "music", "movies", "activities", "personality", "religion", "education", "languages", "values"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    preference = Preference(
        user_id=user_id,
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
    db.session.commit()

    return jsonify({"message": "User and preferences saved successfully"}), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)