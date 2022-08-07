from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError

from api_models import db, connect_db, Beer, Brewery, Style

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hopps_hunter"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "noneofyourbusiness"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)

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


# BEGIN API ROUTES
@app.route('/api/search/beer')
def api_search_beer():
    beers = Beer.query.order_by(Beer.name.asc()).all()
    return render_template('api/beers/index.html', beers=beers)

@app.route('/api/search/brewery')
def api_search_brewery():
    breweries = Brewery.query.order_by(Brewery.name.asc()).all()
    return render_template('api/breweries/index.html', breweries=breweries)

@app.route('/api/search/style')
def api_search_style():
    styles = Style.query.order_by(Style.style_name.asc()).all()
    return render_template('api/styles/index.html', styles=styles)


# END API ROUTES