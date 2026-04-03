from db import db
from sqlalchemy import UniqueConstraint
from werkzeug.security import generate_password_hash, check_password_hash

album_artist = db.Table(
    'album_artist',
    db.Column('album_id', db.Integer, db.ForeignKey('album.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True)
)

track_artist = db.Table(
    'track_artist',
    db.Column('track_id', db.Integer, db.ForeignKey('track.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
    
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mbid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(10))
    image_url = db.Column(db.Text, nullable=True)
    background_url = db.Column(db.Text, nullable=True)
    color_accent = db.Column(db.String(7), nullable=True)  # e.g. '#a4c8e1'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    albums = db.relationship(
        'Album',
        secondary=album_artist,
        back_populates='artists',
        lazy='selectin'
    )

    credits = db.relationship(
        'Credit',
        back_populates='artist',
        lazy='dynamic',
        foreign_keys='Credit.artist_id'
    )

    def __repr__(self):
        return f'<Artist {self.name}>'
    

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mbid = db.Column(db.String(36), nullable=False, unique=True, index=True)
    release_group_mbid = db.Column(db.String(36), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.Date, nullable=True)
    cover_url = db.Column(db.Text, nullable=True)
    color_accent = db.Column(db.String(7), nullable=True)  # e.g. '#c84b38'
    discogs_id = db.Column(db.Integer, nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    artists = db.relationship(
        'Artist',
        secondary=album_artist,
        back_populates='albums',
        lazy='selectin'
    )

    def __repr__(self):
        return f'<Album {self.title} from {self.release_date}>'
    

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mbid = db.Column(db.String(36), nullable=True, unique=True, index=True)
    title = db.Column(db.Text, nullable=False)
    duration_ms = db.Column(db.Integer, nullable=True)
    track_number = db.Column(db.Integer, nullable=False)
    disc_number = db.Column(db.Integer, nullable=False, default=1)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)

    album = db.relationship(
        'Album',
        backref=db.backref(
            'tracks',
            cascade='all, delete-orphan',
            order_by='Track.disc_number, Track.track_number'
        )
    )

    artists = db.relationship(
        'Artist',
        secondary=track_artist,
        lazy='selectin'
    )

    credits = db.relationship(
        'Credit',
        back_populates='track',
        cascade='all, delete-orphan',
        lazy='selectin'
    )

    def __repr__(self):
        return f'<Track {self.track_number}. {self.title}>'


class Credit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False, index=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=True, index=True)
    artist_name = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(64), nullable=False)
    source = db.Column(db.String(16), nullable=False, default='musicbrainz')

    track = db.relationship('Track', back_populates='credits')
    artist = db.relationship('Artist', back_populates='credits', foreign_keys=[artist_id])

    __table_args__ = (
        UniqueConstraint('track_id', 'artist_name', 'role', name='uq_credit_track_artist_role'),
    )

    def __repr__(self):
        return f'<Credit {self.role} — {self.artist_name} on Track {self.track_id}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)
    review_text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='reviews')
    album = db.relationship('Album', backref=db.backref('reviews', cascade='all, delete-orphan'))

    __table_args__ = (
        UniqueConstraint('user_id', 'album_id'),
    )

    def __repr__(self):
        return f'<Review {self.rating} for Album ID {self.album_id} by User ID {self.user_id}>'