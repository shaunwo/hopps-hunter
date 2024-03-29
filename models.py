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
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    deleted_dt = db.Column(db.DateTime,nullable=True)
    __table_args__ = (
        db.UniqueConstraint('beer_id', 'user_id', name='uix_1'),
    )

    @classmethod
    def add(cls, user_id, beer_id):

        wishlist = Wishlist(user_id=user_id, beer_id=beer_id,)
        db.session.add(wishlist)
        return wishlist

    @classmethod
    def delete(cls, user_id, beer_id):

        wishlist = cls.query.filter_by(user_id=user_id, beer_id=beer_id).first()
        wishlist.deleted_dt=datetime.now()
        db.session.commit()
        return wishlist


class User(db.Model):
    
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text,nullable=False,unique=True)
    password = db.Column(db.Text,nullable=False)
    email = db.Column(db.Text,nullable=True,unique=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    location = db.Column(db.Text)
    bio = db.Column(db.Text)
    image_url = db.Column(db.Text)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    last_updated_dt = db.Column(db.DateTime,nullable=False)
    deleted_dt = db.Column(db.DateTime,nullable=True)
    
    wishlist = db.relationship(
        'User',
        secondary='wishlist',
        primaryjoin=(Wishlist.user_id == user_id)
    )

    @classmethod
    def signup(cls, username, password, email):
        """Sign up user.
        Hashes password and adds user to system.
        """
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = User(username=username, password=hashed_pwd, email=email)
        
        db.session.add(user)
        return user
    
    @classmethod
    def changepw(cls, user_id, password):
        """Sign up user.
        Hashes password and adds user to system.
        """
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        user = cls.query.filter_by(user_id=user_id).first()
        user.password=hashed_pwd
        db.session.commit()
        return user

    @classmethod
    def edit(cls, user_id, username, email, first_name, last_name, location, bio, image_url):
        """Update user profile info.
        Hashes password and updates user in system.
        """
        user = cls.query.filter_by(user_id=user_id).first()
        user.username=username
        user.email=email
        user.first_name=first_name
        user.last_name=last_name
        user.location=location
        user.bio=bio
        user.image_url=image_url
        user.last_updated_dt=datetime.now()
        db.session.commit()
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
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    approved_dt = db.Column(db.DateTime,nullable=True)
    deleted_dt = db.Column(db.DateTime,nullable=True)
    __table_args__ = (
        db.UniqueConstraint('connector_user_id', 'connectee_user_id', name='uix_2'),
    )

    @classmethod
    def add(cls, connector_user_id, connectee_user_id):
        follow = UserConnection(connector_user_id=connector_user_id, connectee_user_id=connectee_user_id,)
        
        db.session.add(follow)
        return follow

    @classmethod
    def approve(cls, connector_user_id, connectee_user_id):
        """Update user profile info.
        Hashes password and updates user in system.
        """
        connection = cls.query.filter_by(connector_user_id=connector_user_id, connectee_user_id=connectee_user_id).first()
        connection.last_updated_dt=datetime.now()
        connection.approved_dt=datetime.now()
        db.session.commit()
        return connection


class UserNotification(db.Model):
    
    __tablename__ = 'user_notifications'

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    text = db.Column(db.Text)
    viewed = db.Column(db.Boolean)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())

class Follow(db.Model):
    
    __tablename__ = 'follows'

    follow_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    brewery_id = db.Column(db.Integer,nullable=True)
    beer_id = db.Column(db.Integer,nullable=True)
    style_id = db.Column(db.Integer,nullable=True)
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())

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
    created_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    last_updated_dt = db.Column(db.DateTime,nullable=False,default=datetime.now())
    deleted_dt = db.Column(db.DateTime,nullable=True)

    user = db.relationship("User", primaryjoin="Checkin.user_id == User.user_id")

    @classmethod
    def add(cls, user_id, beer_id, brewery_id, style_id, comments, serving_size, purchase_location, rating, image_url):
        checkin = Checkin(user_id=user_id, beer_id=beer_id, brewery_id=brewery_id, style_id=style_id, comments=comments, serving_size=serving_size, purchase_location=purchase_location, rating=rating, image_url=image_url)
        
        db.session.add(checkin)
        return checkin

    @classmethod
    def edit(cls, checkin_id, comments, serving_size, purchase_location, rating, image_url):
        checkin = cls.query.filter_by(checkin_id=checkin_id).first()
        checkin.comments=comments
        checkin.serving_size=serving_size
        checkin.purchase_location=purchase_location
        checkin.rating=rating
        checkin.image_url=image_url
        checkin.last_updated_dt=datetime.now()
        db.session.commit()
        return checkin
    
    @classmethod
    def delete(cls, checkin_id):
        checkin = cls.query.filter_by(checkin_id=checkin_id).first()
        checkin.deleted_dt=datetime.now()
        db.session.commit()
        return checkin


class CheckinToast(db.Model):
    
    __tablename__ = 'checkin_toasts'

    checkin_toast_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    checkin_id = db.Column(db.Integer,db.ForeignKey('checkins.checkin_id', ondelete='CASCADE'),nullable=False)
    
    user = db.relationship("User", primaryjoin="CheckinToast.user_id == User.user_id")

    @classmethod
    def add(cls, user_id, checkin_id):
        toast = CheckinToast(user_id=user_id, checkin_id=checkin_id)
        
        db.session.add(toast)
        return toast

    def serialize(self):
        
        """Returns a dict representation of checkin toast which we can turn into JSON"""
        
        return {
            'checkin_toast_id': self.checkin_toast_id,
            'user_id': self.user_id,
            'username': self.user.username,
            'checkin_id': self.checkin_id
        }

class CheckinComment(db.Model):
    
    __tablename__ = 'checkin_comments'

    checkin_comment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer,db.ForeignKey('users.user_id', ondelete='CASCADE'),nullable=False)
    checkin_id = db.Column(db.Integer,db.ForeignKey('checkins.checkin_id', ondelete='CASCADE'),nullable=False)
    comments = db.Column(db.Text,nullable=True)
    
    user = db.relationship("User", primaryjoin="CheckinComment.user_id == User.user_id")
    
    @classmethod
    def add(cls, user_id, checkin_id, comments):
        comment = CheckinComment(user_id=user_id, checkin_id=checkin_id, comments=comments)
        
        db.session.add(comment)
        return comment
    
    def serialize(self):
        
        """Returns a dict representation of checkin toast which we can turn into JSON"""
        
        return {
            'checkin_comment_id': self.checkin_comment_id,
            'user_id': self.user_id,
            'username': self.user.username,
            'checkin_id': self.checkin_id,
            'comments': self.comments
        }


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """
    db.app = app
    db.init_app(app)