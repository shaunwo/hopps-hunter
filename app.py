from importlib.resources import as_file
from flask import Flask, render_template, redirect, request, session, flash, g, Markup
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

from models import db, connect_db, User, UserConnection, UserNotification, Follow, Checkin, Toast, ToastComment, Wishlist
from api_models import Beer, Brewery, Style
from forms import SignupForm, LoginForm, SearchForm, BeerCheckinForm

CURR_USER_KEY = "curr_user"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///hopps_hunter"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config["SECRET_KEY"] = "noneofyourbusiness"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)

# displaying home page - sending user to the registration page
@app.route('/')
def home_page():
    
    return redirect('/activity')

##############################################################################
# BEGIN USER SIGNUP/LOGIN/LOGOUT ROUTES 
##############################################################################
@app.before_request
def add_user_to_g():
    """If user is logged in, add Current User to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.user_id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/user/signup', methods=['GET', 'POST'])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = SignupForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
            )
            db.session.commit()

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/user/logout')
def logout():
    
    """Handle logout of user."""

    do_logout()
    flash('You have been logged out. But come back soon!', 'success')
    return redirect("/user/login")

##############################################################################
# END USER SIGNUP/LOGIN/LOGOUT ROUTES 
##############################################################################

# displaying the recent activity
@app.route('/activity')
def activity_page():
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    return render_template('activity/index.html')

# displaying the followers
@app.route('/followers')
def followers_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    return render_template('followers/index.html')

# displaying the profile
@app.route('/profile')
def profile_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    return render_template('profile/index.html')

# displaying the search
@app.route('/search', methods=['GET', 'POST'])
def search_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    form = SearchForm()
    
    if form.validate_on_submit():
        # searching each possible source
        beers = Beer.query.filter(Beer.name.ilike(f"%{form.search.data}%")).order_by(Beer.name.asc()).all()
        breweries = Brewery.query.filter(Brewery.name.ilike(f"%{form.search.data}%")).order_by(Brewery.name.asc()).all()
        styles = Style.query.filter(Style.style_name.ilike(f"%{form.search.data}%")).order_by(Style.style_name.asc()).all()

        if len(beers) == 0 and len(breweries) == 0 and len(styles) == 0:
            flash("Sorry... no matches to that search. Please try another search.", 'danger')

        return render_template('search/index.html', form=form, beers=beers, breweries=breweries, styles=styles)

    else:
        return render_template('search/index.html', form=form)


##############################################################################
# BEGIN BEER/BREWERY/STYLE CHECKIN AND WISHLIST ROUTES 
##############################################################################
@app.route('/beer/checkin/<int:beer_id>', methods=['GET', 'POST'])
def checkin_beer(beer_id):
    beer = Beer.query.get_or_404(beer_id)
    
    form = BeerCheckinForm()

    """ if form.validate_on_submit():
        as_file
        """ 
    
    return render_template('beer/checkin.html', beer=beer, form=form)

@app.route('/beer/wishlist/<int:beer_id>', methods=['GET', 'POST'])
def wishlist_beer(beer_id):
    
    form = SearchForm()

    beer = Beer.query.get_or_404(beer_id)

    try:
        wishlist = Wishlist.add(
            user_id=session[CURR_USER_KEY],
            beer_id=beer_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        message = Markup("Error capturing the wishlist addition. Is it already on your <a href=\"/user/wishlist\">wishlist</a>?")
        flash(message, 'danger')
        return render_template('/search/index.html', form=form)
    
    if wishlist:
        flash(f"{beer.name} added to your wishlist", "success")
    
    return render_template('/search/index.html', form=form)


##############################################################################
# END BEER/BREWERY/STYLE CHECKIN AND WISHLIST ROUTES 
##############################################################################

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