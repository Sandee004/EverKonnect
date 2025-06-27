from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from core.models import db, BlogPost, BlogLike, User

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
  400:
    description: Missing title or content in the request body
    content:
      application/json:
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing title or content"
  401:
    description: Unauthorized - Missing or invalid JWT
    """
    user_id = get_jwt_identity()
    data = request.json
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Missing title or content'}), 400

    post = BlogPost(title=title, content=content, user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Blog post created'}), 201


@blog_bp.route('/blog/posts', methods=['GET'])
def get_posts():
    """
Retrieve all blog posts sorted by newest first.
---
tags:
  - BlogPosts
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
    posts = BlogPost.query.order_by(BlogPost.timestamp.desc()).all()
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
