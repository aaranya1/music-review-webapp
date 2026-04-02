import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from db import db, migrate
from routes.search import search_bp
from routes.users import users_bp
from routes.albums import albums_bp
from routes.artists import artists_bp
from routes.reviews import reviews_bp
from routes.auth import auth_bp
from routes.home import home_bp

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

app.config['JWT_ACCESS_KEY'] = os.getenv('JWT_ACCESS_KEY')
app.config['JWT_REFRESH_KEY'] = os.getenv('JWT_REFRESH_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(search_bp)
app.register_blueprint(users_bp)
app.register_blueprint(albums_bp)
app.register_blueprint(artists_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)
