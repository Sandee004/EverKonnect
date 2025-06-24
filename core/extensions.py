# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flasgger import Swagger
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
swagger = Swagger()
cors = CORS()
bcrypt = Bcrypt()
serializer = URLSafeTimedSerializer("secret_key")
