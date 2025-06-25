from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv
)
from core.config import Config
from core.extensions import db
from core.models import User, BusinessBasicInfo, BusinessCredentials


business_bp = Blueprint('business', __name__)
load_dotenv()


@business_bp.route('/api/business/basic_info', methods=['POST'])
@jwt_required()
def business_registration():
    """
User Business Info Registration
---
tags:
  - Business
security:
  - Bearer: []
consumes:
  - application/json
parameters:
  - name: Authorization
    in: header
    description: "JWT token as: Bearer <your_token>"
    required: true
    type: string
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - fullname
        - home_address
        - phone
        - country
        - state
        - city
        - language
        - sex
        - DoB
        - businessName
        - businessAddress
      properties:
        fullname:
          type: string
          example: John Doe
        home_address:
          type: string
          example: 123 Main Street
        phone:
          type: string
          example: "+1234567890"
        country:
          type: string
          example: "USA"
        state:
          type: string
          example: "California"
        city:
          type: string
          example: "Los Angeles"
        language:
          type: string
          example: "English"
        sex:
          type: string
          example: "Male"
        DoB:
          type: string
          format: date
          example: "1990-01-01"
        businessName:
          type: string
          example: "My Business"
        businessAddress:
          type: string
          example: "456 Market Street"
responses:
  200:
    description: User info updated successfully
  400:
    description: Bad request
  404:
    description: User not found
    """
    # Get user ID from JWT token
    current_user_id = get_jwt_identity()
    
    data = request.json

    # Find the current user
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Get the fields
    fullname = data.get('fullname')
    homeAddress = data.get('home_address')
    phone = data.get('phone')
    country = data.get('country')
    state = data.get('state')
    city = data.get('city')
    language = data.get('language')
    sex = data.get('sex')
    DoB = data.get('DateOfBirth')
    businessName = data.get('businessName')
    businessAddress = data.get('businessAddress')

    required_fields = ["fullname", "address","phone", "country", "state", "city", "language", "sex", "DoB", "businessName", "businessAddress"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    dob = None
    try:
        dob = datetime.strptime(DoB, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return jsonify({"message": "dateOfBirth must be in YYYY-MM-DD format"}), 400

    business_basic_info = user.business_basic_info
    if not business_basic_info:
        business_basic_info = BusinessBasicInfo(
            user_id=user.id
        )

    # Fill the fields
    business_basic_info.fullname = fullname
    business_basic_info.homeAddress = homeAddress
    business_basic_info.phone = phone
    business_basic_info.country = country
    business_basic_info.state = state
    business_basic_info.city = city
    business_basic_info.language = language
    business_basic_info.sex = sex
    business_basic_info.DoB = DoB
    business_basic_info.businessName = businessName
    business_basic_info.businessAddress = businessAddress

    # Add if new record
    if not user.business_basic_info:
        db.session.add(business_basic_info)

    db.session.commit()
    return jsonify({"message": "User info updated successfully"}), 200


@business_bp.route("/api/business/add_credentials", methods=["POST"])
@jwt_required()
def set_business_credentials():
    """
Set User Business Credentials
---
tags:
  - Business
security:
  - Bearer: []
consumes:
  - application/json
parameters:
  - name: Authorization
    in: header
    description: "JWT token as: Bearer <your_token>"
    required: true
    type: string
    example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - profession
        - YearsOfExperience
        - skills
        - description
        - businessInterests
      properties:
        profession:
          type: string
          example: "Software Engineer"
        YearsOfExperience:
          type: integer
          example: 5
        skills:
          type: string
          example: "Python, Flask, SQL"
        description:
          type: string
          example: "Experienced in backend systems and cloud architecture."
        businessInterests:
          type: string
          example: "AI, SaaS, Cloud computing"
responses:
  200:
    description: Credentials updated successfully
  201:
    description: Credentials saved successfully
  400:
    description: Bad request
  404:
    description: User not found
    """
    # Get user ID from JWT token
    current_user_id = get_jwt_identity()
    data = request.json

    # Verify user exists
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    profession = data.get('profession')
    YearsOfExperience = data.get('YearsOfExperience')
    skills = data.get('skills')
    description = data.get('description')
    businessInterests = data.get('businessInterests')

    required_fields = ["profession", "YearsOfExperience", "skills", "description", "businessInterests"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"message": "Fill all fields"}), 400

    # Check if user already has preferences
    existing_credentials = BusinessCredentials.query.filter_by(user_id=current_user_id).first()
    
    if existing_credentials:
        # Update existing preferences
        existing_credentials.profession = profession
        existing_credentials.YearsOfExperience = YearsOfExperience
        existing_credentials.skills = skills
        existing_credentials.description = description
        existing_credentials.businessInterests = businessInterests
        
        message = "Credentials updated successfully"
    else:
        # Create new preferences
        new_credentials = BusinessCredentials(
            user_id=current_user_id,
            profession=profession,
            YearsOfExperience=YearsOfExperience,
            skills=skills,
            descripption=description,
            businessInterests=businessInterests
    
        )
        db.session.add(new_credentials)
        message = "Preferences saved successfully"

    db.session.commit()
    return jsonify({"message": message}), 200


@business_bp.route('/api/business/homepage', methods=['GET'])
def get_users_with_business():
    # inner join returns only users who have a business_basic_info
    users = User.query.join(BusinessBasicInfo).all()

    result = []
    for user in users:
        b = user.business_basic_info
        result.append(
            {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "username": user.username,
                "business_info": {
                    "fullname": b.fullname,
                    "homeAddress": b.homeAddress,
                    "phone": b.phone,
                    "country": b.country,
                    "state": b.state,
                    "city": b.city,
                    "language": b.language,
                    "sex": b.sex,
                    "DoB": b.DoB,
                    "businessName": b.businessName,
                    "businessAddress": b.businessAddress,
                }
            }
        )

    return jsonify(result), 200