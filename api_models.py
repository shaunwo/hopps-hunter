"""SQLAlchemy models for Hopps Hunter"""
from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class Beer(db.Model):
    
    __tablename__ = 'api_beers'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    brewery_id = db.Column(
        db.Integer,
        nullable=False,
    )

    name = db.Column(
        db.Text,
        nullable=False,
    )

    style_id = db.Column(
        db.Integer,
        nullable=False,
    )

    abv = db.Column(
        db.Float,
        nullable=True,
    )

    ibu = db.Column(
        db.Float,
        nullable=True,
    )

    descript = db.Column(
        db.Text,
        nullable=True,
    )

class Brewery(db.Model):
    
    __tablename__ = 'api_breweries'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.Text,
        nullable=False,
    )

    address1 = db.Column(
        db.Text,
        nullable=True,
    )

    address2 = db.Column(
        db.Text,
        nullable=True,
    )

    city = db.Column(
        db.Text,
        nullable=True,
    )

    state = db.Column(
        db.Text,
        nullable=True,
    )

    country = db.Column(
        db.Integer,
        nullable=True,
    )

    descript = db.Column(
        db.Text,
        nullable=True,
    )

class Style(db.Model):
    
    __tablename__ = 'api_styles'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    style_name = db.Column(
        db.Text,
        nullable=False,
    )

def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)

