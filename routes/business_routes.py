from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv
)
from core.config import Config
from core.extensions import db
from core.models import User, BusinessBasicInfo, BusinessCredentials, Connection


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
    business_users = User.query.filter_by(is_business_user=True).all()
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


# Send a connection request
@business_bp.route('/api/connect', methods=['POST'])
def send_connection():
    """
    Send a connection request to another business user.
    ---
    tags:
      - Connections
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sender_id:
              type: integer
              example: 1
            receiver_id:
              type: integer
              example: 2
    responses:
      201:
        description: Connection request sent successfully
      400:
        description: Connection request already exists or both must have business accounts
      404:
        description: User not found
    """
    sender_id = request.json.get('sender_id')
    receiver_id = request.json.get('receiver_id')
    
    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        return jsonify({"error": "User not found"}), 404

    # Check that there's at least one message between the two
    existing_messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).first()

    if not existing_messages:
        return jsonify({"error": "You can only connect with someone you have messaged before."}), 400

    # Check if a connection already exists
    existing_connection = Connection.query.filter(
        ((Connection.sender_id == sender_id) & (Connection.receiver_id == receiver_id)) |
        ((Connection.sender_id == receiver_id) & (Connection.receiver_id == sender_id))
    ).first()
    if existing_connection:
        return jsonify({"error": "Connect request already exists"}), 400

    # Proceed with creating the connection request
    connection = Connection(sender_id=sender_id, receiver_id=receiver_id, status='pending')
    db.session.add(connection)
    db.session.commit()

    return jsonify({"message": "Connection request sent"}), 201

# View pending (received) requests
@business_bp.route('/api/connections/pending/<int:user_id>', methods=['GET'])
def view_pending(user_id):
    """
    Get all pending connection requests received by this user.
    ---
    tags:
      - Connections
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: List of pending connection requests
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 123
                  sender_id:
                    type: integer
                    example: 2
                  status:
                    type: string
                    example: "pending"
    """
    requests_ = Connection.query.filter_by(receiver_id=user_id, status='pending').all()
    result = [
        {
            "id": req.id,
            "sender_id": req.sender_id,
            "status": req.status
        }
        for req in requests_
    ]
    return jsonify(result), 200

# Accept a connection request
@business_bp.route('/connections/accept/<int:connection_id>', methods=['POST'])
def accept_connection(connection_id):
    """
    Accept a pending connection request.
    ---
    tags:
      - Connections
    parameters:
      - name: connection_id
        in: path
        required: true
        schema:
          type: integer
          example: 123
    responses:
      200:
        description: Connection accepted successfully
      404:
        description: Connection not found
    """
    connection = Connection.query.get_or_404(connection_id)
    connection.status = 'accepted'
    db.session.commit()
    return jsonify({"message": "Connection accepted"}), 200

# Decline a connection request
@business_bp.route('/connections/decline/<int:connection_id>', methods=['POST'])
def decline_connection(connection_id):
    """
    Decline a pending connection request.
    ---
    tags:
      - Connections
    parameters:
      - name: connection_id
        in: path
        required: true
        schema:
          type: integer
          example: 123
    responses:
      200:
        description: Connection declined successfully
      404:
        description: Connection not found
    """
    connection = Connection.query.get_or_404(connection_id)
    connection.status = 'declined'
    db.session.commit()
    return jsonify({"message": "Connection declined"}), 200

# View accepted connections
@business_bp.route('/connections/accepted/<int:user_id>', methods=['GET'])
def view_accepted(user_id):
    """
    Get all accepted connections for this user.
    ---
    tags:
      - Connections
    parameters:
      - name: user_id
        in: path
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: List of accepted connections
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  connection_id:
                    type: integer
                    example: 123
                  other_user_id:
                    type: integer
                    example: 2
    """
    connections = Connection.query.filter(
        ((Connection.sender_id == user_id) | (Connection.receiver_id == user_id)) &
        (Connection.status == 'accepted')
    ).all()

    result = []
    for c in connections:
        result.append({
            "connection_id": c.id,
            "other_user_id": c.receiver_id if c.sender_id == user_id else c.sender_id
        })
    return jsonify(result), 200


@business_bp.route('/messages', methods=['POST'])
def send_message():
    """
    Send a message to another user.
    ---
    tags:
      - Messages
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            sender_id:
              type: integer
              example: 1
            receiver_id:
              type: integer
              example: 2
            content:
              type: string
              example: "Hello, how are you?"
    responses:
      201:
        description: Message sent successfully
      404:
        description: User not found
    """
    sender_id = request.json.get('sender_id')
    receiver_id = request.json.get('receiver_id')
    content = request.json.get('content')

    # Validate sender and receiver
    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        return jsonify({"error": "User not found"}), 404

    message = Message(sender_id=sender_id, receiver_id=receiver_id, content=content)
    db.session.add(message)
    db.session.commit()
    return jsonify({"message": "Message sent"}), 201


@business_bp.route('/messages/conversation/<int:sender_id>/<int:receiver_id>', methods=['GET'])
def get_conversation(sender_id, receiver_id):
    """
    Get the conversation between a sender and a receiver.
    ---
    tags:
      - Messages
    parameters:
      - name: sender_id
        in: path
        required: true
        schema:
          type: integer
          example: 1
      - name: receiver_id
        in: path
        required: true
        schema:
          type: integer
          example: 2
    responses:
      200:
        description: List of messages between the sender and receiver
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 100
                  sender_id:
                    type: integer
                    example: 1
                  receiver_id:
                    type: integer
                    example: 2
                  content:
                    type: string
                    example: "Hey, let's connect!"
                  timestamp:
                    type: string
                    example: "2025-06-25T10:30:00"
    """
    messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).order_by(Message.timestamp.asc()).all()

    result = [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat(),
        }
        for msg in messages
    ]
    return jsonify(result), 200
