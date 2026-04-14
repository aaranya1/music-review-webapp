from flask import Blueprint, request, g, make_response
from werkzeug.security import check_password_hash
from functools import wraps
from models import User
from db import db
from tokens import create_access_token, create_refresh_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt, os, re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
limiter = Limiter(get_remote_address, default_limits=["200 per minute"], headers_enabled=True)

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        header = request.headers.get('Authorization')
        if not header or not header.startswith('Bearer '):
            return {"message": "Authorization header is missing or invalid"}, 401
        token = header.split(' ')[1]
        try:
            payload = jwt.decode(token, os.getenv('JWT_ACCESS_KEY'), algorithms=['HS256'])
            g.user_id = int(payload['sub'])
        except jwt.ExpiredSignatureError:
            return {"message": "Token has expired"}, 401
        except jwt.InvalidTokenError:
            return {"message": "Invalid token"}, 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not password or not email:
        return {"message": "Username, email, and password are required"}, 400

    if not _EMAIL_RE.match(email):
        return {"message": "Invalid email address"}, 400

    if len(password) < 8:
        return {"message": "Password must be at least 8 characters"}, 400

    if User.query.filter_by(username=username).first():
        return {"message": "Username already exists"}, 409
    
    if User.query.filter_by(email=email).first():
        return {"message": "An account associated with this email already exists"}, 409

    new_user = User(
        username= username,
        email= email,
    )
    new_user.password = password
    db.session.add(new_user)
    db.session.commit()
    return {"message": "User registered successfully"}, 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return {"message": "Username and password are required"}, 400
    
    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"message": "Invalid username or password"}, 401
    
    access_token = create_access_token(user.id, os.getenv('JWT_ACCESS_KEY'))

    refresh_token = create_refresh_token(user.id, os.getenv('JWT_REFRESH_KEY'))

    response = make_response({
        "access_token": access_token,
        "token_type": "Bearer"
    })

    is_prod = os.getenv('FLASK_ENV') == 'production'
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        secure=is_prod,
        samesite='Strict' if is_prod else 'Lax',
        max_age=7*24*60*60
    )

    return response

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        return {"message": "Missing refresh token"}, 401
    
    try:
        payload = jwt.decode(
            refresh_token,
            os.getenv('JWT_REFRESH_KEY'),
            algorithms=['HS256']
        )
        user_id = int(payload['sub'])
    except jwt.ExpiredSignatureError:
        return {"message": "Refresh token has expired"}, 401
    except jwt.InvalidTokenError:
        return {"message": "Invalid refresh token"}, 401
    
    new_access_token = create_access_token(user_id, os.getenv('JWT_ACCESS_KEY'))

    return {
        "access_token": new_access_token,
        "token_type": "Bearer" }, 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response({"message": "Successfully logged out"})
    response.delete_cookie('refresh_token')
    return response

@auth_bp.route('/me')
@token_required
def get_current_user():
    user_id = g.user_id
    user = User.query.get_or_404(user_id)
    return {"id": user.id, "username": user.username}

