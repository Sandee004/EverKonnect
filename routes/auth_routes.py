from core.imports import (
    request, jsonify, Message,
    create_access_token, JWTManager, get_jwt_identity, jwt_required, render_template,
    datetime, timedelta, random, Client, Blueprint, base64, io, np, Image, cv2, redirect, string, url_for, os, load_dotenv
)
from flask import Flask
from core.config import Config
from core.extensions import db, mail, bcrypt, oauth
from core.models import User, TempUser
from authlib.integrations.flask_client import OAuth
import cloudinary.uploader

auth_bp = Blueprint('auth', __name__)
load_dotenv()

def generate_referral_code(length=8):
    # Generate a random alphanumeric uppercase referral code
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def send_email(to, subject, body):
    msg = Message(subject=subject, recipients=[to])
    msg.html = body
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")

def send_otp_email(email, otp):
    subject = "Your Account Verification OTP"
    body = render_template('email.html', otp=otp, year=datetime.now().year)
    send_email(email, subject, body)


def send_sms_otp(phone, otp):
    account_sid = "your_twilio_sid"
    auth_token = "your_twilio_auth_token"
    client = Client(account_sid, auth_token)

    client.messages.create(
        body=f"Your verification code is {otp}.",
        from_="+1234567890",  # your Twilio number
        to=phone
    )

@auth_bp.route('/api/auth', methods=["POST"])
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

    # Check if user already exists
    existing_user = None
    if email:
        existing_user = User.query.filter_by(email=email).first()
    elif phone:
        existing_user = User.query.filter_by(phone=phone).first()
    
    if existing_user:
        return jsonify({"error": "Account has already been created and verified. Login to continue"}), 400

    try:
        # Check or create temp user
        temp_user = None
        if email:
            temp_user = TempUser.query.filter_by(email=email).first()
        elif phone:
            temp_user = TempUser.query.filter_by(phone=phone).first()

        if not temp_user:
            temp_user = TempUser(email=email, phone=phone)
            db.session.add(temp_user)

        # Generate OTP
        otp = str(random.randint(100000, 999999))
        print(otp)
        temp_user.otp_code = otp
        temp_user.otp_created_at = datetime.utcnow()

        # Attempt to send OTP
        if email:
            send_otp_email(email, otp)
        elif phone:
            send_sms_otp(phone, otp)

        # Only commit if OTP was sent successfully
        db.session.commit()
        print("Added entry to db")
        
        if email:
            return jsonify({"message": f"OTP sent to {email}"}), 200
        else:
            return jsonify({"message": f"OTP sent to {phone}"}), 200

    except Exception as e:
        db.session.rollback()  # Undo any partial DB changes
        print(f"OTP send failed: {e}")
        return jsonify({"error": "Failed to send OTP. Please try again later."}), 500


@auth_bp.route('/api/verify-otp', methods=['POST'])
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
    referral_code = request.json.get('referral_code')

    if not otp or (not email and not phone):
        return jsonify({"error": "OTP and email or phone is required"}), 400

    if email:
        temp_user = TempUser.query.filter_by(email=email, otp_code=otp).first()
    else:
        temp_user = TempUser.query.filter_by(phone=phone, otp_code=otp).first()

    if not temp_user:
        return jsonify({"error": "Invalid email/phone or OTP"}), 404
    
    # Verify OTP
    expiry_time = temp_user.otp_created_at + timedelta(minutes=20)
    if datetime.utcnow() > expiry_time:
        db.session.delete(temp_user)
        db.session.commit()
        return jsonify({"error": "OTP expired. Please request a new one."}), 400

    # Move to real users table
    user = User(email=temp_user.email, phone=temp_user.phone)

    if referral_code:
        referrer = User.query.filter_by(referral_code=referral_code).first()
        if referrer:
            referrer.referral_points += 5
        else:
            return jsonify({"error": "Invalid referral code"}), 400
        
    user.referral_code = generate_referral_code()
    db.session.add(user)
    db.session.delete(temp_user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    return jsonify({
        "message": "OTP verified successfully",
        "access_token": access_token,
        "user_id": user.id,
        "referral_code": user.referral_code,
    }), 200


@auth_bp.route('/api/set-credentials', methods=['POST'])
@jwt_required()
def set_credentials():
    """
Set user credentials (username and password)
---
tags:
  - Authentication
security:
  - Bearer: []
parameters:
  - name: Authorization
    in: header
    description: JWT token as Bearer <your_token>
    required: true
    type: string
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  - name: body
    in: body
    required: true
    schema:
      type: object
      properties:
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
    # Get user ID from JWT token
    current_user_id = get_jwt_identity()
    
    username = request.json.get('username')
    password = request.json.get('password')

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    user = User.query.get(current_user_id)
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


@auth_bp.route('/api/upload-profile-pic', methods=['POST'])
@jwt_required()
def upload_profile_pic():
    """
    Upload user profile picture
    ---
    tags:
      - User
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - name: Authorization
        in: header
        type: string
        required: true
        description: JWT token as Bearer <your_token>
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: face_image
        in: formData
        type: file
        required: true
        description: Profile image file to upload
    responses:
      200:
        description: Profile picture uploaded successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Profile picture uploaded successfully"
            image_url:
              type: string
              example: "https://res.cloudinary.com/your-cloud/image/upload/v1234/profile.jpg"
      400:
        description: Missing image file
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No image file provided"
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "User not found"
      500:
        description: Upload failed
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Upload failed: something went wrong"
    """
    user_id = get_jwt_identity()

    if 'face_image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['face_image']

    try:
        upload_result = cloudinary.uploader.upload(image_file)
        image_url = upload_result.get("secure_url")

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        user.profile_pic = image_url
        db.session.commit()

        return jsonify({
            "message": "Profile picture uploaded successfully",
            "image_url": image_url
        }), 200

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """
    Login with username/email and password
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            identifier:
              type: string
              example: "username or email"
            password:
              type: string
              format: password
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            access_token:
              type: string
            user_id:
              type: integer
      401:
        description: Invalid credentials
    """
    identifier = request.json.get('identifier')  # Can be username or email
    password = request.json.get('password')
    print(password)

    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user:
        print("User not found")
        return jsonify({"error": "Invalid credentials"}), 401

    print("User found:", user.username)
    print("Stored hash:", user.password_hash)

    if not bcrypt.check_password_hash(user.password_hash, password):
        print("Password mismatch")
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    return jsonify({"access_token": access_token, "user_id": user.id}), 200


@auth_bp.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    Get current user profile
    ---
    tags:
      - User
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
        description: User profile retrieved successfully
      404:
        description: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data = {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "profile": user.profile_pic,
        "username": user.username,
        "nickname": user.nickname,
        "fullname": user.fullname,
        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
        "age_range": user.age_range,
        "marital_status": user.marital_status,
        "country_of_origin": user.country_of_origin,
        "tribe": user.tribe,
        "current_location": user.current_location,
        "skin_tone": user.skin_tone
    }
    
    return jsonify(user_data), 200




linkedin = oauth.register(
    name='linkedin',
    client_id = os.getenv("LINKEDIN_CLIENT_ID"),
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET"),
    access_token_url='https://www.linkedin.com/oauth/v2/accessToken',
    authorize_url='https://www.linkedin.com/oauth/v2/authorization',
    client_kwargs={'scope': 'r_liteprofile r_emailaddress'}
)

@auth_bp.route('/api/linkedin/login', methods=['GET'])
def linkedin_login():
    """Redirect the user to LinkedIn's authorization page"""
    redirect_uri = url_for('auth.linkedin_callback', _external=True)
    return linkedin.authorize_redirect(redirect_uri)

@auth_bp.route('/api/linkedin/callback', methods=['GET'])
def linkedin_callback():
    """Handle the callback from LinkedIn"""
    token = linkedin.authorize_access_token()
    # Fetch profile info
    profile = linkedin.get('https://api.linkedin.com/v2/me').json()
    email_data = linkedin.get(
        'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'
    ).json()

    # Extract data
    first_name = profile.get('localizedFirstName')
    last_name = profile.get('localizedLastName')
    email = email_data['elements'][0]['handle~']['emailAddress']
    referral_code = request.args.get('referral_code')

    # Check if user exists or create
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=f"{first_name}_{last_name}")

        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                referrer.referral_points += 5  # Award 5 points
            else:
                return jsonify({"error": "Invalid referral code"}), 400
            
        user.referral_code = generate_referral_code()
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24)
    )

    return jsonify(
        message="Login successful",
        access_token=access_token,
        user_id=user.id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        referral_code=user.referral_code
    ), 200


google = oauth.register(
    name='google',
    client_id = os.getenv("GOOGLE_CLIENT_ID"),
    client_secret = os.getenv("GOGGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    client_kwargs={'scope': 'openid profile email'},
)

@auth_bp.route('/api/google/login')
def google_login():
    """Redirect user to Google's OAuth consent screen."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/api/google/callback')
def google_callback():
    """Handle Google's callback with auth code and fetch profile info."""
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    profile = resp.json()
    email = profile.get('email')
    first_name = profile.get('given_name')
    last_name = profile.get('family_name')
    picture = profile.get('picture')
    google_id = profile.get('id')

    referral_code = request.args.get('referral_code')

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=email.split('@')[0])

        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                referrer.referral_points += 5  # Award 5 points
            else:
                return jsonify({"error": "Invalid referral code"}), 400
            
        user.referral_code = generate_referral_code()
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24)
    )

    return jsonify(
        message='Login successful',
        access_token=access_token,
        user_id=user.id,
        email=email,
        first_name=first_name,
        last_name=last_name,
        picture=picture,
        google_id=google_id,
        referral_code=user.referral_code
    ), 200


facebook = oauth.register(
    name='facebook',
    client_id = os.getenv("FACEBOOK_APP_ID"),
    client_secret = os.getenv("FACEBOOK_APP_SECRET"),
    access_token_url='https://graph.facebook.com/v17.0/oauth/access_token',
    authorize_url='https://www.facebook.com/v17.0/dialog/oauth',
    api_base_url='https://graph.facebook.com/v17.0/',
    client_kwargs={'scope': 'email,public_profile'},
)

@auth_bp.route('/api/facebook/login')
def facebook_login():
    return facebook.authorize_redirect(
        redirect_uri=url_for('auth.facebook_callback', _external=True)
    )

@auth_bp.route('/api/facebook/callback')
def facebook_callback():
    token = facebook.authorize_access_token()
    resp = facebook.get('me?fields=id,name,email')
    profile = resp.json()

    email = profile.get('email')
    facebook_id = profile.get('id')
    name = profile.get('name')

    referral_code =  request.args.get('referral_code')

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=name)

        if referral_code:
            referrer = User.query.filter_by(referral_code=referral_code).first()
            if referrer:
                referrer.referral_points += 5  # Award 5 points
            else:
                return jsonify({"error": "Invalid referral code"}), 400
            
        user.referral_code = generate_referral_code()
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify(
        message='Login successful',
        access_token=access_token,
        user_id=user.id,
        email=email,
        name=name,
        facebook_id=facebook_id,
        referral_code=user.referral_code
    )
