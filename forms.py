from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length

# user / account routes
class SignupForm(FlaskForm):
    """Form for signing up/creating new account"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

class LoginForm(FlaskForm):
    """Login form"""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])

# search / checkin ; wishlist forms
class SearchForm(FlaskForm):
    """Search form"""

    search = StringField('search', validators=[DataRequired()])

class BeerCheckinForm(FlaskForm):
    """Beer checkin form"""

    comments = TextAreaField("Content")