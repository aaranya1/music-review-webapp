import jwt
import time

def create_access_token(user_id, secret):
    now = time.time()
    payload = {
        'sub': str(user_id),
        'iat': now,
        'exp': now + 30 * 60
    }

    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def create_refresh_token(user_id, secret):
    now = time.time()
    payload = {
        'sub': str(user_id),
        'iat': now,
        'exp': now + 7 * 24 * 60 * 60
    }

    token = jwt.encode(payload, secret, algorithm='HS256')
    return token