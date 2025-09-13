from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from core.models import db, BlogPost, BlogLike, User, BlogComment, BusinessBasicInfo
import cloudinary.uploader

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/blog/create', methods=['POST'])
@jwt_required()
def create_post():
    """
    Create a new blog post by the authenticated user.
    ---
    tags:
      - BlogPosts
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
      - name: body
        in: body
        description: Blog post details
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "My First Blog Post"
            content:
              type: string
              example: "This is the content of my blog post."
    responses:
      201:
        description: Blog post created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Blog post created"
                post:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 101
                    title:
                      type: string
                      example: "My First Blog Post"
                    content:
                      type: string
                      example: "This is the content of my blog post."
                    author:
                      type: string
                      example: "Anonymous123"
                    timestamp:
                      type: string
                      format: date-time
                      example: "2025-06-27T14:32:00Z"
      400:
        description: Missing title or content in the request body
      401:
        description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json or {}
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Missing title or content'}), 400

    # Create the blog post
    post = BlogPost(title=title, content=content, user_id=user_id)
    db.session.add(post)
    db.session.commit()

    # Resolve author's display name (anonymous or real)
    business_info = BusinessBasicInfo.query.filter_by(user_id=user.id).first()
    if business_info and business_info.isAnonymous and business_info.anonymousProfile:
        author_name = business_info.anonymousProfile.username
    else:
        author_name = user.username

    # Return post info with resolved author
    return jsonify({
        'message': 'Blog post created',
        'post': {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'timestamp': post.timestamp.isoformat() if post.timestamp else None
        }
    }), 201


@blog_bp.route('/blog/posts', methods=['GET'])
@jwt_required()
def get_posts():
    """
    Retrieve blog posts restricted to the authenticated user's account type.
    ---
    tags:
      - BlogPosts
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
    responses:
      200:
        description: List of blog posts
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 101
                  title:
                    type: string
                    example: "My First Blog Post"
                  content:
                    type: string
                    example: "This is the content of my blog post."
                  author:
                    type: string
                    example: "johndoe"
                  timestamp:
                    type: string
                    format: date-time
                    example: "2025-06-27T14:32:00Z"
                  likes:
                    type: integer
                    example: 5
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    posts = (
        BlogPost.query
        .join(User)
        .filter(User.account_type == user.account_type)
        .order_by(BlogPost.timestamp.desc())
        .all()
    )

    result = [{
        'id': p.id,
        'title': p.title,
        'content': p.content,
        'author': p.author.username,
        'timestamp': p.timestamp.isoformat(),
        'likes': len(p.likes)
    } for p in posts]

    return jsonify(result), 200


@blog_bp.route('/blog/<int:post_id>/like', methods=['POST'])
@jwt_required()
def like_post(post_id):
    """
Like a blog post by the authenticated user.
---
tags:
  - Blog
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
  - name: post_id
    in: path
    type: integer
    required: true
    description: ID of the blog post to like
    example: 123
responses:
  200:
    description: Post was already liked by the user
    content:
      application/json:
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Already liked"
  201:
    description: Post liked successfully
    content:
      application/json:
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Post liked"
  401:
    description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    existing_like = BlogLike.query.filter_by(user_id=user_id, post_id=post_id).first()
    if existing_like:
        return jsonify({'message': 'Already liked'}), 200

    like = BlogLike(user_id=user_id, post_id=post_id)
    db.session.add(like)
    db.session.commit()
    return jsonify({'message': 'Post liked'}), 201


@blog_bp.route('/blog/<int:post_id>/comment', methods=['POST'])
@jwt_required()
def add_comment(post_id):
    """
    Add a comment to a blog post.
    ---
    tags:
      - BlogComments
    security:
      - Bearer: []
    parameters:
      - name: Authorization
        in: header
        description: 'JWT token as: Bearer <your_token>'
        required: true
        schema:
          type: string
      - name: post_id
        in: path
        required: true
        description: ID of the blog post to add comments
        schema:
          type: integer
      - name: content
        in: formData
        type: string
        description: Text comment (optional for business users if uploading a file)
        required: false
      - name: file
        in: formData
        type: file
        description: File upload (only for business users)
        required: false
    responses:
      201:
        description: Comment added successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Comment added successfully"
                comment:
                  type: object
                  properties:
                    id:
                      type: integer
                      example: 201
                    content:
                      type: string
                      example: "Great post!"
                    file_url:
                      type: string
                      example: "https://res.cloudinary.com/.../upload/sample.jpg"
                    author:
                      type: string
                      example: "Anonymous123"
                    timestamp:
                      type: string
                      format: date-time
                      example: "2025-09-13T15:22:00Z"
      400:
        description: Missing comment content or file
      404:
        description: Post not found
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    post = BlogPost.query.get(post_id)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    content = request.form.get('content')
    file_url = None

    # Allow file uploads only for business accounts
    if user.account_type == "business" and "file" in request.files:
        file = request.files["file"]
        if file:
            upload_result = cloudinary.uploader.upload(file)
            file_url = upload_result.get("secure_url")

    if not content and not file_url:
        return jsonify({"error": "Content or file required"}), 400

    # Save the comment
    comment = BlogComment(
        content=content,
        file_url=file_url,
        post_id=post.id,
        user_id=user.id
    )
    db.session.add(comment)
    db.session.commit()

    # Resolve author's display name
    business_info = BusinessBasicInfo.query.filter_by(user_id=user.id).first()
    if business_info and business_info.isAnonymous and business_info.anonymousProfile:
        author_name = business_info.anonymousProfile.username
    else:
        author_name = user.username

    return jsonify({
        "message": "Comment added successfully",
        "comment": {
            "id": comment.id,
            "content": comment.content,
            "file_url": comment.file_url,
            "timestamp": comment.timestamp.isoformat() if comment.timestamp else None
        }
    }), 201


@blog_bp.route('/blog/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    View comments on a blog post.
    ---
    tags:
      - BlogComments
    parameters:
      - name: post_id
        in: path
        required: true
        description: ID of the blog post to fetch comments for
        schema:
          type: integer
    responses:
      200:
        description: List of comments
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 12
              user:
                type: string
                example: "janedoe"
              content:
                type: string
                example: "This is so helpful, thanks!"
              file_url:
                type: string
                example: "https://res.cloudinary.com/demo/image/upload/v1234567890/file.pdf"
              timestamp:
                type: string
                format: date-time
                example: "2025-08-01T15:45:00Z"
      404:
        description: Blog post not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Post not found"
    """
    post = BlogPost.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    comments = BlogComment.query.filter_by(post_id=post_id).order_by(BlogComment.timestamp.asc()).all()
    result = [{
        'id': c.id,
        'user': c.user.username,
        'content': c.content,
        'file_url': c.file_url,  # include uploaded file if any
        'timestamp': c.timestamp.isoformat()
    } for c in comments]

    return jsonify(result), 200
