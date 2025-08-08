import os
from dotenv import load_dotenv
import cloudinary

load_dotenv()


class Config:
    """Configuration class for the Flask application"""
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    #SQLALCHEMY_DATABASE_URI = "sqlite:///everkonnect.db"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    MAIL_SERVER = 'smtp.zoho.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("USERNAME_FOR_EMAIL")
    MAIL_PASSWORD = os.getenv("PASSWORD_FOR_EMAIL")
    MAIL_DEFAULT_SENDER = os.getenv("USERNAME_FOR_EMAIL")


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

    
