from core.imports import time, os, request, uuid, jsonify, Blueprint, SocketIO, or_
from core.models import db, Call
from agora_token_builder import RtcTokenBuilder
from flask_jwt_extended import jwt_required, get_jwt_identity

call_bp = Blueprint("call", __name__)

AGORA_APP_ID = os.getenv("AGORA_APP_ID")
AGORA_APP_CERTIFICATE = os.getenv("AGORA_APP_CERTIFICATE")


def generate_agora_token(channel_name: str, uid: int, role="publisher"):
    expiration_time_in_seconds = 3600
    current_timestamp = int(time.time())
    privilege_expired_ts = current_timestamp + expiration_time_in_seconds
    role_type = 1 if role == "publisher" else 2

    token = RtcTokenBuilder.buildTokenWithUid(
        AGORA_APP_ID, AGORA_APP_CERTIFICATE, channel_name, uid, role_type, privilege_expired_ts
    )
    return token

socketio = SocketIO(cors_allowed_origins="*")
connected_users = {}

# ✅ Socket.IO Events
@socketio.on("connect")
def handle_connect():
    print("⚡ Client connected")

@socketio.on("register")
def handle_register(data):
    user_id = str(data.get("user_id"))
    if user_id:
        connected_users[user_id] = request.sid
        print(f"✅ Registered user {user_id} with sid {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    for uid, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[uid]
            print(f"❌ User {uid} disconnected")

# -----------------------
# Initiate Call
# -----------------------
@call_bp.route("/call/initiate", methods=["POST"])
@jwt_required()
def initiate_call():
    """
    Initiate a new voice or video call
    ---
    tags:
      - Calls
    parameters:
      - name: Authorization
        in: header
        description: JWT token as Bearer <your_token>
        required: true
        type: string
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            receiver_id:
              type: string
              example: "45"
            call_type:
              type: string
              enum: [voice, video]
              example: "voice"
    responses:
      201:
        description: Call initiated successfully
        schema:
          type: object
          properties:
            call_id:
              type: integer
              example: 101
            channel_name:
              type: string
              example: "call_a1b2c3d4"
            agora_token:
              type: string
            app_id:
              type: string
            status:
              type: string
              example: "initiated"
    """
    data = request.get_json()
    caller_id = str(get_jwt_identity())
    receiver_id = str(data.get("receiver_id"))
    call_type = data.get("call_type", "voice")

    channel_name = f"call_{uuid.uuid4().hex[:8]}"
    token = generate_agora_token(channel_name, uid=int(caller_id))

    call = Call(caller_id=caller_id, receiver_id=receiver_id, channel_name=channel_name)
    db.session.add(call)
    db.session.commit()

    if receiver_id in connected_users:
        socketio.emit(
            "incoming_call",
            {
                "call_id": call.id,
                "caller_id": caller_id,
                "channel_name": channel_name,
                "call_type": call_type,
            },
            to=connected_users[receiver_id],
        )
        print(f"📞 Notified receiver {receiver_id} of incoming call")

    return jsonify({
        "call_id": call.id,
        "channel_name": channel_name,
        "agora_token": token,
        "app_id": AGORA_APP_ID,
        "status": call.status,
    }), 201


# -----------------------
# Accept Call
# -----------------------
@call_bp.route("/call/accept", methods=["POST"])
@jwt_required()
def accept_call():
    """
    Accept an incoming call
    ---
    tags:
      - Calls
    parameters:
      - name: Authorization
        in: header
        description: JWT token as Bearer <your_token>
        required: true
        type: string
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            call_id:
              type: integer
              example: 101
    responses:
      200:
        description: Call accepted successfully
        schema:
          type: object
          properties:
            channel_name:
              type: string
            agora_token:
              type: string
            app_id:
              type: string
            status:
              type: string
              example: "accepted"
    """
    data = request.get_json()
    receiver_id = str(get_jwt_identity())
    call_id = data.get("call_id")

    call = Call.query.get(call_id)
    if not call or str(call.receiver_id) != receiver_id:
        return jsonify({"error": "Invalid call"}), 400

    call.status = "accepted"
    db.session.commit()

    token = generate_agora_token(call.channel_name, uid=int(receiver_id))
    caller_id = str(call.caller_id)

    if caller_id in connected_users:
        socketio.emit(
            "call_accepted",
            {"call_id": call.id, "receiver_id": receiver_id},
            to=connected_users[caller_id],
        )
        print(f"✅ Caller {caller_id} notified: call accepted")

    return jsonify({
        "channel_name": call.channel_name,
        "agora_token": token,
        "app_id": AGORA_APP_ID,
        "status": call.status,
    })


# -----------------------
# Decline Call
# -----------------------
@call_bp.route("/call/decline", methods=["POST"])
@jwt_required()
def decline_call():
    """
    Decline an incoming call
    ---
    tags:
      - Calls
    parameters:
      - name: Authorization
        in: header
        description: JWT token as Bearer <your_token>
        required: true
        type: string
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            call_id:
              type: integer
              example: 101
    responses:
      200:
        description: Call declined successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Call declined"
    """
    data = request.get_json()
    receiver_id = str(get_jwt_identity())
    call_id = data.get("call_id")

    call = Call.query.get(call_id)
    if not call or str(call.receiver_id) != receiver_id:
        return jsonify({"error": "Invalid call"}), 400

    call.status = "declined"
    db.session.commit()

    caller_id = str(call.caller_id)
    if caller_id in connected_users:
        socketio.emit(
            "call_declined",
            {"call_id": call.id, "receiver_id": receiver_id},
            to=connected_users[caller_id],
        )
        print(f"❌ Caller {caller_id} notified: call declined")

    return jsonify({"message": "Call declined"})


# -----------------------
# End Call
# -----------------------
@call_bp.route("/call/end", methods=["POST"])
@jwt_required()
def end_call():
    """
    End an ongoing call
    ---
    tags:
      - Calls
    parameters:
      - name: Authorization
        in: header
        description: JWT token as Bearer <your_token>
        required: true
        type: string
        example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6..."
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            call_id:
              type: integer
              example: 101
    responses:
      200:
        description: Call ended successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Call ended"
      404:
        description: Call not found
    """
    data = request.get_json()
    user_id = str(get_jwt_identity())
    call_id = data.get("call_id")

    call = Call.query.get(call_id)
    if not call:
        return jsonify({"error": "Call not found"}), 404

    call.status = "ended"
    db.session.commit()

    participants = [str(call.caller_id), str(call.receiver_id)]
    for pid in participants:
        if pid in connected_users and pid != user_id:
            socketio.emit(
                "call_ended",
                {"call_id": call.id, "ended_by": user_id},
                to=connected_users[pid],
            )

    print(f"📴 Call {call.id} ended by user {user_id}")

    return jsonify({"message": "Call ended"})


@call_bp.route("/call/history", methods=["GET"])
@jwt_required()
def call_history():
    """
    Get call history for the current user
    ---
    tags:
      - Calls
    parameters:
      - name: Authorization
        in: header
        description: JWT token
        required: true
        type: string
    responses:
      200:
        description: List of past calls
        schema:
          type: array
          items:
            type: object
            properties:
              call_id:
                type: integer
              direction:
                type: string
                enum: [incoming, outgoing]
              other_party:
                type: string
              status:
                type: string
              category:
                type: string
                description: derived status (picked, missed)
              timestamp:
                type: string
    """
    current_user_id = int(get_jwt_identity())

    calls = Call.query.filter(
        or_(Call.caller_id == current_user_id, Call.receiver_id == current_user_id)
    ).order_by(Call.created_at.desc()).all()

    history_data = []

    for call in calls:
        if call.caller_id == current_user_id:
            direction = "outgoing"
            other_user = call.receiver
        else:
            direction = "incoming"
            other_user = call.caller

        if call.status in ['accepted', 'ended']:
            category = "picked"
        elif call.status in ['declined', 'missed']:
            category = "missed"
        elif call.status == 'ringing':
            category = "missed"
        else:
            category = "unknown"

        history_data.append({
            "call_id": call.id,
            "direction": direction,
            "other_party_id": other_user.id if other_user else None,
            "other_party_name": other_user.username if other_user and hasattr(other_user, 'username') else "Unknown",
            "status": call.status,
            "category": category,
            "created_at": call.created_at.isoformat()
        })

    return jsonify(history_data), 200

