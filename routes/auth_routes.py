from core.imports import (
    request, jsonify, Message,
    create_access_token, JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, random, Client, Blueprint, base64, io, np, Image, cv2
)
from flask import Flask
from core.config import Config
from core.extensions import db, mail, bcrypt
from core.models import User, TempUser


auth_bp = Blueprint('auth', __name__)


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
    
    # Check if user already exists in main users table
    existing_user = None
    if email:
        existing_user = User.query.filter_by(email=email).first()
    elif phone:
        existing_user = User.query.filter_by(phone=phone).first()
    
    if existing_user:
        return jsonify({"error": "User already exists"}), 400
    
    # Find or create temp user
    temp_user = None
    if email:
        temp_user = TempUser.query.filter_by(email=email).first()
    elif phone:
        temp_user = TempUser.query.filter_by(phone=phone).first()
    
    if not temp_user:
        temp_user = TempUser(email=email, phone=phone)
        db.session.add(temp_user)
    
    # Generate and save OTP
    otp = str(random.randint(100000, 999999))
    print(otp)
    temp_user.otp_code = otp
    temp_user.otp_created_at = datetime.utcnow()
    db.session.commit()
    print("Added entry to db")
    
    if email:
        subject = "Your verification code"
        body = f"<p>Your verification code is <strong>{otp}</strong></p>"
        send_email_otp(email, subject, body)
        return jsonify({"message": f"OTP sent to {email}"}), 200
    elif phone:
        send_sms_otp(phone, otp)
        return jsonify({"message": f"OTP sent to {phone}"}), 200


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

    if not otp or (not email and not phone):
        return jsonify({"error": "OTP and email or phone is required"}), 400

    temp_user = None
    if email:
        temp_user = TempUser.query.filter_by(email=email).first()
    elif phone:
        temp_user = TempUser.query.filter_by(phone=phone).first()
    
    if not temp_user:
        return jsonify({"error": "User not found"}), 404
    
    # Verify OTP
    expiry_time = temp_user.otp_created_at + timedelta(minutes=5)
    if temp_user.otp_code != otp:
        return jsonify({"error": "Invalid OTP"}), 400
    elif datetime.utcnow() > expiry_time:
        return jsonify({"error": "OTP expired"}), 400
    
    # Move to main users table
    user = User(email=temp_user.email, phone=temp_user.phone)
    db.session.add(user)
    
    # Delete from temp table
    db.session.delete(temp_user)
    db.session.commit()

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=24))
    return jsonify({
        "message": "OTP verified successfully",
        "access_token": access_token,
        "user_id": user.id
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


@auth_bp.route('/api/verify-face', methods=['POST'])
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

    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400

    # Find user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

    if not user or not user.password_hash:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Create access token
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=24)
    )

    return jsonify({
        "access_token": access_token,
        "user_id": user.id
    }), 200


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
