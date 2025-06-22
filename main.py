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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)