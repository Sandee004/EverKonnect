# models.py
from .extensions import db
from datetime import datetime

class TempUser(db.Model):
    __tablename__ = 'temp_users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
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
