from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///flask_feedback"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "noneofyourbusiness"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

# displaying home page - sending user to the registration page
@app.route('/')
def home_page():
    
    return redirect('/activity')

# displaying the recent activity
@app.route('/activity')
def activity_page():
    return render_template('activity/index.html')

# displaying the followers
@app.route('/followers')
def followers_page():
    return render_template('followers/index.html')

# displaying the profile
@app.route('/profile')
def profile_page():
    return render_template('profile/index.html')

# displaying the search
@app.route('/search')
def search_page():
    return render_template('search/index.html')