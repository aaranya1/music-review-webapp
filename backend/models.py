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


class ReviewLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('User', backref='review_likes')
    review = db.relationship('Review', backref=db.backref('likes', cascade='all, delete-orphan'))

    __table_args__ = (
        UniqueConstraint('user_id', 'review_id'),
    )

    def __repr__(self):
        return f'<ReviewLike user={self.user_id} review={self.review_id}>'


class ReviewComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    media_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('User', backref='review_comments')
    review = db.relationship('Review', backref=db.backref('comments', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ReviewComment id={self.id} review={self.review_id} user={self.user_id}>'


class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('review_comment.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('User', backref='comment_likes')
    comment = db.relationship('ReviewComment', backref=db.backref('likes', cascade='all, delete-orphan'))

    __table_args__ = (
        UniqueConstraint('user_id', 'comment_id'),
    )

    def __repr__(self):
        return f'<CommentLike user={self.user_id} comment={self.comment_id}>'


class Backlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('User', backref='backlog')
    album = db.relationship('Album', backref='backlogged_by')

    __table_args__ = (
        UniqueConstraint('user_id', 'album_id'),
    )

    def __repr__(self):
        return f'<Backlog user={self.user_id} album={self.album_id}>'


class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    following = db.relationship('User', foreign_keys=[following_id], backref='followers')

    __table_args__ = (
        UniqueConstraint('follower_id', 'following_id'),
    )

    def __repr__(self):
        return f'<Follow {self.follower_id} → {self.following_id}>'


class List(db.Model):
    __tablename__ = 'list'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='lists')
    items = db.relationship(
        'ListItem',
        back_populates='list',
        cascade='all, delete-orphan',
        order_by='ListItem.position'
    )

    def __repr__(self):
        return f'<List {self.id} "{self.title}" by user {self.user_id}>'


class ListItem(db.Model):
    __tablename__ = 'list_item'

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('list.id'), nullable=False, index=True)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    note = db.Column(db.Text, nullable=True)

    list = db.relationship('List', back_populates='items')
    album = db.relationship('Album', backref='list_items')

    __table_args__ = (
        UniqueConstraint('list_id', 'album_id'),
    )

    def __repr__(self):
        return f'<ListItem list={self.list_id} album={self.album_id} pos={self.position}>'


class Notification(db.Model):
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    type = db.Column(db.String(32), nullable=False)
    target_type = db.Column(db.String(32), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    actor = db.relationship('User', foreign_keys=[actor_id])

    __table_args__ = (
        UniqueConstraint('user_id', 'actor_id', 'type', 'target_type', 'target_id',
                         name='uq_notification_dedupe'),
    )

    def __repr__(self):
        return f'<Notification {self.type} to={self.user_id} from={self.actor_id}>'