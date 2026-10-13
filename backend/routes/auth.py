from flask import Blueprint, request, g, make_response
from werkzeug.security import check_password_hash
from functools import wraps
from sqlalchemy import func
from models import User
from db import db
from tokens import create_access_token, create_refresh_token
from extensions import limiter
from request_utils import get_json_body
import jwt, os, re

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
# 3-30 chars of a-z 0-9 _ . with at least one letter, so a username can never
# be all digits and collide with the /users/<int:user_id> route.
_USERNAME_RE = re.compile(r'^(?=.*[a-z])[a-z0-9_.]{3,30}$')
_EMAIL_MAX_LEN = 120  # matches User.email column

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


def optional_auth(f):
    """Set g.user_id from a valid Bearer token if present, else None. Never rejects."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.user_id = None
        header = request.headers.get('Authorization')
        if header and header.startswith('Bearer '):
            try:
                payload = jwt.decode(header.split(' ')[1], os.getenv('JWT_ACCESS_KEY'), algorithms=['HS256'])
                g.user_id = int(payload['sub'])
            except jwt.InvalidTokenError:
                pass
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = get_json_body()

    username = (data.get('username') or '').strip().lower()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not username or not password or not email:
        return {"message": "Username, email, and password are required"}, 400

    if not _USERNAME_RE.match(username):
        return {"message": "Username must be 3-30 characters of letters, numbers, _ or ., "
                           "and include at least one letter"}, 400

    if len(email) > _EMAIL_MAX_LEN or not _EMAIL_RE.match(email):
        return {"message": "Invalid email address"}, 400

    if not isinstance(password, str) or len(password) < 8:
        return {"message": "Password must be at least 8 characters"}, 400

    # Case-insensitive, so existing mixed-case accounts still block look-alikes
    if User.query.filter(func.lower(User.username) == username).first():
        return {"message": "Username already exists"}, 409

    if User.query.filter(func.lower(User.email) == email).first():
        return {"message": "An account associated with this email already exists"}, 409

    new_user = User(
        username= username,
        email= email,
    )
    new_user.password = password
    db.session.add(new_user)
    db.session.commit()
    return {"message": "User registered successfully"}, 201


def _refresh_cookie_attrs():
    is_prod = os.getenv('FLASK_ENV') == 'production'
    return {
        'httponly': True,
        'secure': is_prod,
        'samesite': 'Strict' if is_prod else 'Lax',
    }


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per hour")
def login():
    data = get_json_body()
    username = (data.get('username') or '').strip()
    password = data.get('password')

    if not username or not isinstance(password, str) or not password:
        return {"message": "Username and password are required"}, 400

    user = User.query.filter(func.lower(User.username) == username.lower()).first()

    if not user or not check_password_hash(user.password_hash, password):
        return {"message": "Invalid username or password"}, 401
    
    access_token = create_access_token(user.id, os.getenv('JWT_ACCESS_KEY'))

    refresh_token = create_refresh_token(user.id, os.getenv('JWT_REFRESH_KEY'))

    response = make_response({
        "access_token": access_token,
        "token_type": "Bearer"
    })

    response.set_cookie(
        'refresh_token',
        refresh_token,
        max_age=7*24*60*60,
        **_refresh_cookie_attrs()
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
    # Must match the attributes used when setting it, or some browsers keep the cookie
    response.delete_cookie('refresh_token', **_refresh_cookie_attrs())
    return response

@auth_bp.route('/me')
@token_required
def get_current_user():
    user_id = g.user_id
    user = User.query.get_or_404(user_id)
    return {"id": user.id, 
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at}

