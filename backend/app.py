import os
from datetime import date, datetime
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from db import db, migrate
from extensions import limiter
from routes.search import search_bp
from routes.users import users_bp
from routes.albums import albums_bp
from routes.artists import artists_bp
from routes.reviews import reviews_bp
from routes.auth import auth_bp
from routes.home import home_bp
from routes.backlog import backlog_bp
from routes.follows import follows_bp
from routes.lists import lists_bp
from routes.notifications import notifications_bp

load_dotenv()

# Fail fast on missing secrets rather than erroring on the first login
_REQUIRED_ENV = ('DATABASE_URI', 'JWT_ACCESS_KEY', 'JWT_REFRESH_KEY')
_missing = [name for name in _REQUIRED_ENV if not os.getenv(name)]
if _missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")


class ISODateJSONProvider(DefaultJSONProvider):
    """Serialize dates as ISO 8601 instead of Flask's default RFC 822 format."""
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


app = Flask(__name__)
app.json = ISODateJSONProvider(app)

# Behind a reverse proxy, trust X-Forwarded-* from that many hops so the rate
# limiter sees real client IPs. Leave at 0 when not behind a proxy, otherwise
# clients could spoof X-Forwarded-For to dodge rate limits.
_proxy_hops = int(os.getenv('TRUSTED_PROXY_HOPS', '0'))
if _proxy_hops:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=_proxy_hops, x_proto=_proxy_hops, x_host=_proxy_hops)

_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS(app, supports_credentials=True, origins=[o.strip() for o in _origins])

app.config['JWT_ACCESS_KEY'] = os.getenv('JWT_ACCESS_KEY')
app.config['JWT_REFRESH_KEY'] = os.getenv('JWT_REFRESH_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# memory:// keeps a separate count per Gunicorn worker; set a redis:// URI to share limits
app.config['RATELIMIT_STORAGE_URI'] = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

db.init_app(app)
migrate.init_app(app, db)

limiter.init_app(app)


@app.errorhandler(429)
def ratelimit_handler(_e):
    return jsonify({"message": "Too many requests, please slow down."}), 429


@app.errorhandler(HTTPException)
def http_error_handler(e):
    return jsonify({"message": e.description}), e.code


_PG_UNIQUE_VIOLATION = '23505'


@app.errorhandler(IntegrityError)
def integrity_error_handler(e):
    # Concurrent duplicate submits (double-clicked review, like, follow, signup)
    # pass the "already exists" check and then hit the unique constraint.
    db.session.rollback()
    if getattr(e.orig, 'pgcode', None) == _PG_UNIQUE_VIOLATION:
        return jsonify({"message": "That already exists."}), 409
    app.logger.exception("Database integrity error")
    return jsonify({"message": "Internal server error"}), 500


@app.errorhandler(Exception)
def unhandled_error_handler(e):
    db.session.rollback()
    app.logger.exception("Unhandled error")
    return jsonify({"message": "Internal server error"}), 500


@app.route('/health')
@limiter.exempt
def health():
    return {"status": "ok"}


@app.route('/health/ready')
@limiter.exempt
def health_ready():
    try:
        db.session.execute(db.text('SELECT 1'))
        return {"status": "ready"}
    except Exception:
        return {"status": "db_unavailable"}, 503

app.register_blueprint(search_bp)
app.register_blueprint(users_bp)
app.register_blueprint(albums_bp)
app.register_blueprint(artists_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
app.register_blueprint(backlog_bp)
app.register_blueprint(follows_bp)
app.register_blueprint(lists_bp)
app.register_blueprint(notifications_bp)
