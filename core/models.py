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
    profile_pic = db.Column(db.Text, nullable=True)
    username = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True) 
    referral_code = db.Column(db.String(20), unique=True, nullable=True)  # e.g. "ABC123"
    referral_points = db.Column(db.Integer, default=0, nullable=False)
    account_type = db.Column(db.String(20), nullable=True)

    love_basic_info = db.relationship('LoveBasicInfo', backref='user', uselist=False, lazy='joined')
    personality = db.relationship('UserPersonality', backref='user', uselist=False, lazy='joined')
    matchpreference = db.relationship('MatchPreference', backref='user', uselist=False, lazy='joined')
    business_basic_info = db.relationship('BusinessBasicInfo', backref='user', uselist=False, lazy='joined')
    business_credentials = db.relationship('BusinessCredentials', backref='user', uselist=False, lazy='joined')
    saved_images = db.relationship('SavedPhoto', backref='user', lazy='select')  # or 'dynamic'
    blog_posts = db.relationship('BlogPost', backref='author', lazy='select')

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
    links = db.Column(db.JSON, nullable=True)

    isAnonymous = db.Column(db.Boolean, default=False)
    anonymousProfile = db.relationship('BusinessAnonymous', backref='business_basic_info', uselist=False)

class BusinessCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    profession = db.Column(db.String(250), nullable=True)
    YearsOfExperience = db.Column(db.Integer, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    businessInterests = db.Column(db.Text, nullable=True)

class BusinessAnonymous(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), nullable=True)

    business_id = db.Column(db.Integer, db.ForeignKey('business_basic_info.id'), nullable=False)


class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'accepted', 'declined'

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_connections')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_connections')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])


class SavedPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)  # e.g. "uploads/myimage.png"
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('BlogLike', backref='post', lazy=True)

class BlogLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)

class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)  # optional if file is uploaded
    file_url = db.Column(db.String(500), nullable=True)  # for Cloudinary uploads
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user = db.relationship('User', backref='blog_comments')
    post = db.relationship('BlogPost', backref='comments')
