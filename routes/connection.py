from core.imports import (
    request, jsonify, Message,
    JWTManager, get_jwt_identity, jwt_required,
    datetime, timedelta, Blueprint, redirect, load_dotenv
)
from core.config import Config
from core.extensions import db
from core.models import User, Connection

connection_bp = Blueprint('connection', __name__)
load_dotenv()

# Send a connection request
@connection_bp.route('/api/connect', methods=['POST'])
@jwt_required()
def send_connection():
    """
    Send a connection request to another user, if at least one message exists between them.
    ---
    tags:
      - Connections
    security:
      - Bearer: []
    consumes:
      - application/json
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
          example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - receiver_id
          properties:
            receiver_id:
              type: integer
              description: ID of the user to connect with
              example: 456
    responses:
      201:
        description: Connection request successfully sent
        schema:
          type: object
          properties:
            message:
              type: string
              example: Connection request sent
      400:
        description: Bad request (e.g. no prior messages or existing connection)
        schema:
          type: object
          properties:
            error:
              type: string
              example: "You can only connect with someone you have messaged before."
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "User not found"
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    sender_id = get_jwt_identity()
    receiver_id = request.json.get('receiver_id')

    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)
    if not sender or not receiver:
        return jsonify({"error": "User not found"}), 404

    existing_messages = Message.query.filter(
        ((Message.sender_id == sender_id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == sender_id))
    ).first()

    if not existing_messages:
        return jsonify({"error": "You can only connect with someone you have messaged before."}), 400

    existing_connection = Connection.query.filter(
        ((Connection.sender_id == sender_id) & (Connection.receiver_id == receiver_id)) |
        ((Connection.sender_id == receiver_id) & (Connection.receiver_id == sender_id))
    ).first()
    if existing_connection:
        return jsonify({"error": "Connect request already exists"}), 400

    connection = Connection(sender_id=sender_id, receiver_id=receiver_id, status='pending')
    db.session.add(connection)
    db.session.commit()

    return jsonify({"message": "Connection request sent"}), 201


# View pending (received) requests
@connection_bp.route('/api/connections/pending', methods=['GET'])
@jwt_required()
def view_pending():
    """
    View all pending connection requests received by the authenticated user.
    ---
    tags:
      - Connections
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
        description: List of pending connection requests
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
                example: 456
              status:
                type: string
                example: pending
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
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
@connection_bp.route('/connections/accept/<int:connection_id>', methods=['POST'])
def accept_connection(connection_id):
    """
    Accept a pending business connection request.
    ---
    tags:
      - Connections
    parameters:
      - name: connection_id
        in: path
        type: integer
        required: true
        description: The ID of the connection to accept
    responses:
      200:
        description: Connection successfully accepted
        schema:
          type: object
          properties:
            message:
              type: string
              example: Connection accepted
      404:
        description: Connection not found
    """
    connection = Connection.query.get_or_404(connection_id)
    connection.status = 'accepted'
    db.session.commit()
    return jsonify({"message": "Connection accepted"}), 200


# Decline a connection request
@connection_bp.route('/connections/decline/<int:connection_id>', methods=['POST'])
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
@connection_bp.route('/connections/accepted', methods=['GET'])
@jwt_required()
def view_accepted():
    """
    View all accepted business connections for the authenticated user.
    ---
    tags:
      - Connections
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
        description: A list of accepted connections
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
                example: 456
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    connections = Connection.query.filter(
        ((Connection.sender_id == user_id) | (Connection.receiver_id == user_id)) &
        (Connection.status == 'accepted')
    ).all()

    result = [
        {
            "connection_id": c.id,
            "other_user_id": c.receiver_id if c.sender_id == user_id else c.sender_id
        }
        for c in connections
    ]
    return jsonify(result), 200
