from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, RadioField
from wtforms.validators import DataRequired, Email, Length, Optional

##################################################
##  BEGIN USER / ACCOUNT FORMS
##################################################
class SignupForm(FlaskForm):
    """Form for signing up/creating new account"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
    email = StringField('Email', validators=[DataRequired(), Email()])

class LoginForm(FlaskForm):
    """Login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
##################################################
##  END USER / ACCOUNT FORMS
##################################################


##################################################
##  BEGIN SEARCH / CHECKIN FORMS
##################################################
class SearchForm(FlaskForm):
    """Search form"""
    SEARCH_FOR_CHOICES = ['Beer', 'Brewery', 'Style', 'ALL']
    search = StringField('search', validators=[DataRequired()])
    searchfor = SelectField(u'', choices=SEARCH_FOR_CHOICES )

class BeerCheckinForm(FlaskForm):
    """Beer checkin form"""
    comments = TextAreaField("Comments")
    SERVING_STYLE_CHOICES = ['Draft','Bottle','Can','Taster','Cask','Crowler','Growler']
    serving_size = SelectField(u'Serving Style', choices=SERVING_STYLE_CHOICES )
    purchase_location = StringField('Purchase Location')
    RATING_CHOICES = ['0.0','0.5','1.0','1.5','2.0','2.5','3.0','3.5','4.0','4.5','5.0']
    rating = SelectField(u'Rating', choices=RATING_CHOICES )
    image_url = StringField('Image')

class CheckinCommentsForm(FlaskForm):
    """Checkin comments form"""
    comments = TextAreaField("Comments")
##################################################
##  END SEARCH / CHECKIN FORMS
##################################################


##################################################
##  BEGIN PROFILE-RELATED FORMS 
##################################################
class EditProfileForm(FlaskForm):
    """Form for editing a user profile"""
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    location = StringField('Location')
    bio = TextAreaField('Bio', validators=[DataRequired()])
    image_url = StringField('Image', validators=[DataRequired()])

class ChangePWForm(FlaskForm):
    """Form for changing the PW for a user's account"""
    current_password = PasswordField('Current Password', validators=[Length(min=6)])
    new_password = PasswordField('New Password', validators=[Length(min=6)])
    new_password_confirm = PasswordField('Confirm New Password', validators=[Length(min=6)])
##################################################
##  END PROFILE-RELATED FORMS 
##################################################
