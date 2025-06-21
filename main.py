from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from flask_cors import CORS
from datetime import timedelta, datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydatabase.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)

jwt = JWTManager(app)
db = SQLAlchemy(app)
CORS(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)


@app.route('/')
def home():
    return "Home"

@app.route('/api/auth', methods=["POST"])
def auth():
    username = request.json.get('username')
    email = request.json.get('email')
    phone = request.json.get('phone')
    print("Data gotten")

    if not username or not email:
        return jsonify({"message": "Fill all fields"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        if user.username != username or user.email != email:
            return jsonify({"message": "Invalid credentials"}), 400
        
        print("Okayyy. Login")
        access_token = create_access_token(identity=user.id)
        return jsonify({"message": "Login successful", "access_token": access_token}), 200
    
    print("Okayyyy. Sign up")
    new_user = User(username=username, email=email, phone=phone)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)
    return jsonify({"message": "User created successfully", "access_token": access_token}), 201


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)