from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

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

class EditProfileForm(FlaskForm):
    """Form for editing a user profile"""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    zip_code = StringField('Zip Code')
    bio = TextAreaField('Bio', validators=[DataRequired()])
    private = BooleanField('Private?', validators=[Optional()])
    image_url = StringField('Image', validators=[DataRequired()])

class ChangePWForm(FlaskForm):
    """Form for changing the PW for a user's account"""
    current_password = PasswordField('Current Password', validators=[Length(min=6)])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    new_password_confirm = PasswordField('Confirm New Password', validators=[Length(min=6)])
