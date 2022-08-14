"""SQLAlchemy models for Hopps Hunter core application"""
from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class Wishlist(db.Model):
    
    __tablename__ = 'wishlist'

    wishlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    beer_id = db.Column(db.Integer,nullable=False)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)
    __table_args__ = (
        db.UniqueConstraint('beer_id', 'user_id', name='uix_1'),
    )

    @classmethod
    def add(cls, user_id, beer_id):
        wishlist = Wishlist(user_id=user_id, beer_id=beer_id,)
        
        db.session.add(wishlist)
        return wishlist


class User(db.Model):
    
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text,nullable=False,unique=True)
    password = db.Column(db.Text,nullable=False)
    email = db.Column(db.Text,nullable=True,unique=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    zip_code = db.Column(db.Text)
    bio = db.Column(db.Text)
    private = db.Column(db.Boolean)
    image_url = db.Column(db.Text,default="/static/images/default-pic.png")
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)
    
    wishlist = db.relationship(
        'User',
        secondary='wishlist',
        primaryjoin=(Wishlist.user_id == user_id)
    )

    @classmethod
    def signup(cls, username, password):
        """Sign up user.
        Hashes password and adds user to system.
        """
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = User(username=username, password=hashed_pwd,)
        
        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.
        This is a class method (call it on the class, not an individual user.)It searches for a user whose password hash matches this passwordand, if it finds such a user, returns that user object.
        If can't find matching user (or if password is wrong), returns False."""
        user = cls.query.filter_by(username=username).first()
        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class UserConnection(db.Model):
    
    __tablename__ = 'user_connections'

    connection_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    connector_user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    connectee_user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)

class UserNotification(db.Model):
    
    __tablename__ = 'user_notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    text = db.Column(db.Text)
    viewed = db.Column(db.Boolean)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())

class Follow(db.Model):
    
    __tablename__ = 'follows'

    follow_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    brewery_id = db.Column(db.Integer,nullable=True)
    beer_id = db.Column(db.Integer,nullable=True)
    style_id = db.Column(db.Integer,nullable=True)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)

class Checkin(db.Model):
    
    __tablename__ = 'checkins'

    checkin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    brewery_id = db.Column(db.Integer,nullable=False)
    beer_id = db.Column(db.Integer,nullable=False)
    style_id = db.Column(db.Integer,nullable=False)
    comments = db.Column(db.Text,nullable=True)
    serving_size = db.Column(db.String,nullable=True)
    purchase_location = db.Column(db.Text,nullable=True)
    rating = db.Column(db.Float,nullable=True)
    image_url = db.Column(db.String,nullable=True)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)

class Toast(db.Model):
    
    __tablename__ = 'toasts'

    toast_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    checkin_id = db.Column(db.Integer,db.ForeignKey('checkins.checkin_id', ondelete='CASCADE'),nullable=False)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)

class ToastComment(db.Model):
    
    __tablename__ = 'toast_comments'

    toast_comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    toast_id = db.Column(db.Integer,db.ForeignKey('toasts.toast_id', ondelete='CASCADE'),nullable=False)
    comments = db.Column(db.Text,nullable=True)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.utcnow())
    deleted_dt = db.Column(db.DateTime,nullable=True)

def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)