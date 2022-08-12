"""SQLAlchemy models for Hopps Hunter API"""
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

class Beer(db.Model):
    
    __tablename__ = 'api_beers'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
    )

    brewery_id = db.Column(
        db.Integer,
        db.ForeignKey('api_breweries.id'),
        nullable=False,
    )

    name = db.Column(
        db.Text,
        nullable=False,
    )

    style_id = db.Column(
        db.Integer,
        db.ForeignKey('api_styles.id'),
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

    brewery = db.relationship("Brewery", primaryjoin="Beer.brewery_id == Brewery.id")
    style = db.relationship("Style", primaryjoin="Beer.style_id == Style.id")

class Brewery(db.Model):
    
    __tablename__ = 'api_breweries'

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
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
        autoincrement=True,
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

