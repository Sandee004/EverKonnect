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

    love_basic_info = db.relationship('LoveBasicInfo', backref='user', uselist=False)
    personality = db.relationship('UserPersonality', backref='user', uselist=False)
    matchpreference = db.relationship('MatchPreference', backref='user', uselist=False)
    business_basic_info = db.relationship('BusinessBasicInfo', backref='user', uselist=False)
    business_credentials = db.relationship('BusinessCredentials', backref='user', uselist=False)

class LoveBasicInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    nickname = db.Column(db.String(100), nullable=True)
    fullname = db.Column(db.String(250), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    age_range = db.Column(db.String(50), nullable=True)
    marital_status = db.Column(db.String(50), nullable=True)
    country_of_origin = db.Column(db.String(100), nullable=True)
    tribe = db.Column(db.String(100), nullable=True)
    current_location = db.Column(db.String(100), nullable=True)
    skin_tone = db.Column(db.String(50), nullable=True)


class UserPersonality(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    height = db.Column(db.String(250), nullable=True)
    eye_colour = db.Column(db.String(250), nullable=True)
    body_type = db.Column(db.String(250), nullable=True)
    hair_colour = db.Column(db.String(250), nullable=True)
    hair_style = db.Column(db.String(250), nullable=True)
    interest = db.Column(db.Text, nullable=True)
    hobbies = db.Column(db.Text, nullable=True)
    music = db.Column(db.Text, nullable=True)
    movies = db.Column(db.Text, nullable=True)
    activities = db.Column(db.Text, nullable=True)
    personality = db.Column(db.Text, nullable=True)
    religion = db.Column(db.String(250), nullable=True)
    education = db.Column(db.String(250), nullable=True)
    languages = db.Column(db.String(250), nullable=True)
    values = db.Column(db.Text, nullable=True)


class MatchPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    age_range = db.Column(db.String(50), nullable=True)
    marital_status = db.Column(db.String(50), nullable=True)
    country_of_origin = db.Column(db.String(100), nullable=True)
    tribe = db.Column(db.String(100), nullable=True)
    current_location = db.Column(db.String(100), nullable=True)
    skin_tone = db.Column(db.String(50), nullable=True)
    height = db.Column(db.String(250), nullable=True)
    eye_colour = db.Column(db.String(250), nullable=True)
    body_type = db.Column(db.String(250), nullable=True)
    hair_colour = db.Column(db.String(250), nullable=True)
    hair_style = db.Column(db.String(250), nullable=True)
    religion = db.Column(db.String(250), nullable=True)
    education = db.Column(db.String(250), nullable=True)
    languages = db.Column(db.Text, nullable=True)
    values = db.Column(db.Text, nullable=True)
    interest = db.Column(db.Text, nullable=True)
    hobbies = db.Column(db.Text, nullable=True)
    music = db.Column(db.Text, nullable=True)
    movies = db.Column(db.Text, nullable=True)
    activities = db.Column(db.Text, nullable=True)
    personality = db.Column(db.String(250), nullable=True)

class BusinessBasicInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    fullname = db.Column(db.String(250), nullable=True)
    homeAddress = db.Column(db.String(250), nullable=True)
    phone = db.Column(db.String(250), nullable=True)
    country = db.Column(db.String(250), nullable=True)
    state = db.Column(db.String(250), nullable=True)
    city = db.Column(db.String(250), nullable=True)
    language = db.Column(db.Text, nullable=True)
    sex = db.Column(db.String(250), nullable=True)
    DoB = db.Column(db.String(250), nullable=True)
    businessName = db.Column(db.String(250), nullable=True)
    businessAddress = db.Column(db.String(250), nullable=True)

class BusinessCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    profession = db.Column(db.String(250), nullable=True)
    YearsOfExperience = db.Column(db.Integer, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    businessInterests = db.Column(db.Text, nullable=True)

