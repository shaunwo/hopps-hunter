from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

# user / account routes
class SignupForm(FlaskForm):
    """Form for signing up/creating new account"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    email = StringField('Email', validators=[DataRequired(), Email()])

class LoginForm(FlaskForm):
    """Login form"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

# search / checkin ; wishlist forms
class SearchForm(FlaskForm):
    """Search form"""
    SEARCH_FOR_CHOICES = [('Beer', 'Beer'), ('Brewery', 'Brewery'), ('Style', 'Style'), ('ALL', 'ALL')]

    search = StringField('search', validators=[DataRequired()])
    searchfor = SelectField(u'', choices=SEARCH_FOR_CHOICES )

class BeerCheckinForm(FlaskForm):
    """Beer checkin form"""

    comments = TextAreaField("Content")