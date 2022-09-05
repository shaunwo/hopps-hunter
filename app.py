from ast import MatchSequence
from curses.ascii import NUL
from importlib.resources import as_file
from pickle import FALSE
from flask import Flask, render_template, redirect, request, session, flash, g, Markup, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import Unauthorized
from werkzeug.utils import secure_filename

import json, requests, boto3, os, mimetypes
from os import getenv

s3 = boto3.client('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY'), aws_secret_access_key= os.getenv('AWS_SECRET_ACCESS_KEY'))

BUCKET_NAME='hopps-hunter'

from models import db, connect_db, User, UserConnection, Checkin, CheckinToast, CheckinComment, Wishlist
from api_models import Beer, Brewery, Style
from forms import SignupForm, LoginForm, SearchForm, BeerCheckinForm, EditProfileForm, ChangePWForm, CheckinCommentsForm

CURR_USER_KEY = "curr_user"
USER_WISHLIST = "wishlist"
USER_FOLLOWING = "following"
USER_FOLLOWERS = "followers"
BASE_API_URL = os.environ.get('BASE_API_URL','http://127.0.0.1:5000/api')
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL', 'postgresql:///hopps_hunter').replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'noneofyourbusiness')
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)
bcrypt = Bcrypt()

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

    # adding items on user's wishlist to session
    wishlist_ids = Wishlist.query.filter(Wishlist.user_id == session[CURR_USER_KEY], Wishlist.deleted_dt == None).with_entities(Wishlist.beer_id).order_by(Wishlist.created_dt.desc()).all()
    session[USER_WISHLIST] = [id for id, in wishlist_ids]
    
    # adding user's following to session
    following_ids = UserConnection.query.filter(UserConnection.connector_user_id == session[CURR_USER_KEY], UserConnection.approved_dt != None).with_entities(UserConnection.connectee_user_id).order_by(UserConnection.created_dt.desc()).all()
    session[USER_FOLLOWING] = [id for id, in following_ids]

    # adding user's followers to session
    followers_ids = UserConnection.query.filter(UserConnection.connectee_user_id == session[CURR_USER_KEY], UserConnection.approved_dt != None).with_entities(UserConnection.connector_user_id).order_by(UserConnection.created_dt.desc()).all()
    session[USER_FOLLOWERS] = [id for id, in followers_ids]

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
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)
        flash(f"Welcome to Hopps Hunter, {user.username}!", "success")
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
            flash(f"Welcome back, {user.username}!", "success")
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


##############################################################################
# BEGIN ACTIVITY ROUTES 
##############################################################################

# displaying the recent activity
@app.route('/activity')
def activity_page():
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    form = CheckinCommentsForm()

    # pulling beer IDs for recent checkins
    activity_beers = (Checkin.query
                .filter(Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.beer_id)
                .all())
    activity_beer_ids = [id for id, in activity_beers]
    
    q_string = ''
    for beer_id in activity_beer_ids:
        q_string += "&ids="
        q_string += beer_id.__str__()

    res = requests.get(f"{BASE_API_URL}/beers?{q_string}")
    data = res.content
    data_array = json.loads(data)

    beers = {}

    # creating an array of beers from the API data
    for beer in data_array['beers']:

        beers[beer['id']] = {
            'beer_id': beer['id'],
            'name': beer['name'],
            'brewery': beer['brewery'],
            'style': beer['style'],
            'abv': beer['abv'],
            'descript': beer['descript']
        }
    
    # creating an list of checkin ids to create tuples of toasts and comments
    checkins = (Checkin.query
                .filter(Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.checkin_id)
                .all())
    checkin_ids = [id for id, in checkins]
    
    # creating tuple of toasts
    checkin_toasts = [toasts.serialize() for toasts in CheckinToast.query.filter(CheckinToast.checkin_id.in_(checkin_ids)).all()]
    toasts= {}
    for toast in checkin_toasts:
        toasts[toast['checkin_id']] = toasts.get(toast['checkin_id'], ()) + ({
            'user_id': toast['user_id'],
            'username': toast['username']
        },)

    # creating tuple of comments
    checkin_comments = [comments.serialize() for comments in CheckinComment.query.filter(CheckinComment.checkin_id.in_(checkin_ids)).all()]
    comments= {}
    for comment in checkin_comments:
        comments[comment['checkin_id']] = comments.get(comment['checkin_id'], ()) + ({
            'user_id': comment['user_id'],
            'username': comment['username'],
            'comments': comment['comments']
        },)
    
    # pulling recent checkins
    ratings = (Checkin.query
                .filter(Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .all())
 
    return render_template('activity/index.html', ratings=ratings, form=form, beers=beers, toasts=toasts, comments=comments)


# displaying the activity on a specific beer
@app.route('/activity/beer/<int:beer_id>')
def beer_activity_page(beer_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    form = CheckinCommentsForm()
    
    # pulling single result from the API
    res = requests.get(f"{BASE_API_URL}/beer/{beer_id}")
    data = res.content
    data_array = json.loads(data)

    beers = {}
    
    for beer in data_array['beers']:

        beers[beer['id']] = {
            'beer_id': beer['id'],
            'name': beer['name'],
            'brewery': beer['brewery'],
            'style': beer['style'],
            'abv': beer['abv'],
            'descript': beer['descript']
        }
    
    # creating an list of checkin ids to create tuples of toasts and comments
    checkins = (Checkin.query
                .filter(Checkin.beer_id==beer_id, Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.checkin_id)
                .all())
    checkin_ids = [id for id, in checkins]
    
    # creating tuple of toasts
    checkin_toasts = [toasts.serialize() for toasts in CheckinToast.query.filter(CheckinToast.checkin_id.in_(checkin_ids)).all()]
    toasts= {}
    for toast in checkin_toasts:
        toasts[toast['checkin_id']] = toasts.get(toast['checkin_id'], ()) + ({
            'user_id': toast['user_id'],
            'username': toast['username']
        },)

    # creating tuple of comments
    checkin_comments = [comments.serialize() for comments in CheckinComment.query.filter(CheckinComment.checkin_id.in_(checkin_ids)).all()]
    comments= {}
    for comment in checkin_comments:
        comments[comment['checkin_id']] = comments.get(comment['checkin_id'], ()) + ({
            'user_id': comment['user_id'],
            'username': comment['username'],
            'comments': comment['comments']
        },)

    # pulling recent checkins
    ratings = (Checkin.query
                .filter(Checkin.beer_id==beer_id, Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .all())

    return render_template('activity/index.html', form=form, ratings=ratings, beers=beers, beer_id=beer_id, toasts=toasts, comments=comments)

# displaying the recent activity for ONE user
@app.route('/activity/<int:user_id>', methods=['GET'])
def user_activity_page(user_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    form = CheckinCommentsForm()
    user = User.query.get_or_404(user_id)

    # pulling beer IDs for recent checkins
    activity_beers = (Checkin.query
                .filter(Checkin.user_id==user_id, Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.beer_id)
                .all())
    activity_beer_ids = [id for id, in activity_beers]
    
    q_string = ''
    for beer_id in activity_beer_ids:
        q_string += "&ids="
        q_string += beer_id.__str__()

    res = requests.get(f"{BASE_API_URL}/beers?{q_string}")
    data = res.content
    data_array = json.loads(data)

    beers = {}

    for beer in data_array['beers']:

        beers[beer['id']] = {
            'beer_id': beer['id'],
            'name': beer['name'],
            'brewery': beer['brewery'],
            'style': beer['style'],
            'abv': beer['abv'],
            'descript': beer['descript']
        }

    # creating an list of checkin ids to create tuples of toasts and comments
    checkins = (Checkin.query
                .filter(Checkin.user_id==user_id)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.checkin_id)
                .all())
    checkin_ids = [id for id, in checkins]
    
    # creating tuple of toasts
    checkin_toasts = [toasts.serialize() for toasts in CheckinToast.query.filter(CheckinToast.checkin_id.in_(checkin_ids)).all()]
    toasts= {}
    for toast in checkin_toasts:
        toasts[toast['checkin_id']] = toasts.get(toast['checkin_id'], ()) + ({
            'user_id': toast['user_id'],
            'username': toast['username']
        },)

    # creating tuple of comments
    checkin_comments = [comments.serialize() for comments in CheckinComment.query.filter(CheckinComment.checkin_id.in_(checkin_ids)).all()]
    comments= {}
    for comment in checkin_comments:
        comments[comment['checkin_id']] = comments.get(comment['checkin_id'], ()) + ({
            'user_id': comment['user_id'],
            'username': comment['username'],
            'comments': comment['comments']
        },)

    # pulling recent checkins
    ratings = (Checkin.query
                .filter(Checkin.user_id==user_id, Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .all())

    return render_template('activity/index.html', ratings=ratings, user=user, form=form, beers=beers, toasts=toasts, comments=comments)

# toast someone else's checkin
@app.route('/activity/toast/<int:checkin_id>', methods=['GET'])
def checkin_toast(checkin_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    try:
        toast = CheckinToast.add(
            user_id=session[CURR_USER_KEY],
            checkin_id=checkin_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        message = Markup("Error capturing the toast addition. Please try again.")
        flash(message, 'danger')
        return redirect(request.referrer)
    
    if toast:
        flash(f"Thanks for your toast!", "success")
        return redirect(request.referrer)

    return render_template('activity/index.html')

# leave a comment on someone else's checkin
@app.route('/activity/comment/<int:checkin_id>', methods=['POST'])
def checkin_comment(checkin_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    checkin = Checkin.query.get_or_404(checkin_id)
    form = CheckinCommentsForm(obj=checkin)
    
    try:
        comment = CheckinComment.add(
            user_id=session[CURR_USER_KEY],
            checkin_id=checkin_id,
            comments=form.comments.data,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        message = Markup("Error capturing the comments addition. Please try again.")
        flash(message, 'danger')
        return redirect(request.referrer)
    
    if comment:
        flash(f"Thanks for your comment!", "success")
        return redirect(request.referrer)

    return render_template('activity/index.html')

# displaying the profile for another use to follow
@app.route('/activity/profile/<int:user_id>', methods=['GET'])
def other_profile_page(user_id):

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    # pulling profile info
    profile = User.query.get_or_404(user_id)
    
    return render_template('activity/profile.html', profile=profile)

# follow someone
@app.route('/activity/follow/<int:connectee_user_id>', methods=['GET'])
def follow_user(connectee_user_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    follow = User.query.get_or_404(connectee_user_id)

    try:
        connection = UserConnection.add(
            connector_user_id=session[CURR_USER_KEY],
            connectee_user_id=connectee_user_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        message = Markup("Error capturing the follow request. Did you already try to follow that person?")
        flash(message, 'danger')
        return redirect(f'/activity/profile/{connectee_user_id}')
    
    if connection:
        session[USER_FOLLOWING].append(connectee_user_id)
        flash(f"Follow request sent for {follow.username}", "success")
    
    return redirect(f'/activity/profile/{connectee_user_id}')

# follow someone
@app.route('/activity/unfollow/<int:connectee_user_id>', methods=['GET'])
def unfollow_user(connectee_user_id):

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")

    user = User.query.get_or_404(connectee_user_id)

    try:
        db.session.query(UserConnection).filter(UserConnection.connectee_user_id==connectee_user_id).delete()
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error deleting from the database. Please try again.", 'danger')
        return redirect(f'/activity/profile/{connectee_user_id}')

    session[USER_FOLLOWING].remove(connectee_user_id)
    flash(f"You have unfollowed {user.username}.", "success")

    return redirect(f'/activity/profile/{connectee_user_id}')

##############################################################################
# END ACTIVITY ROUTES 
##############################################################################


##############################################################################
# BEGIN FOLLOWERS/FRIENDS ROUTES 
##############################################################################

# displaying the followers
@app.route('/followers')
def followers_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    # pulling pending follow requests
    pending_followers = (UserConnection.query
                .filter(UserConnection.connectee_user_id==session[CURR_USER_KEY], UserConnection.approved_dt == None)
                .with_entities(UserConnection.connector_user_id)
                .order_by(UserConnection.created_dt.desc())
                .all())
    pending_followers_ids = [id for id, in pending_followers]
    
    pending_users = (User.query
            .filter(User.user_id.in_(pending_followers_ids))).all()

    # pulling approved follow requests
    approved_followers = (UserConnection.query
                .filter(UserConnection.connectee_user_id==session[CURR_USER_KEY], UserConnection.approved_dt != None)
                .with_entities(UserConnection.connector_user_id)
                .order_by(UserConnection.created_dt.desc())
                .all())
    approved_followers_ids = [id for id, in approved_followers]
    
    approved_users = (User.query
            .filter(User.user_id.in_(approved_followers_ids))).all()

    return render_template('followers/index.html', pending_users=pending_users, approved_users=approved_users)

@app.route('/followers/block/<int:connector_user_id>')
def block_follower(connector_user_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    user = User.query.get_or_404(connector_user_id)

    # deleting follow requests
    try:
        db.session.query(UserConnection).filter(UserConnection.connector_user_id==connector_user_id, UserConnection.connectee_user_id==session[CURR_USER_KEY]).delete()
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error saving to the database. Please try again.", 'danger')
        return redirect('/profile/checkins')

    session[USER_FOLLOWERS].remove(connector_user_id)
    flash(f"You have blocked {user.username}.", "success")
    return redirect("/followers")

@app.route('/followers/approve/<int:user_id>')
def approve_follower(user_id):

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")

    try:
        connection = UserConnection.approve(
            connectee_user_id=session['curr_user'],
            connector_user_id=user_id,
        )

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error saving to the database. Please try again.", 'danger')
        return redirect('/followers')

    flash(f"Follower approved!", "success")
    return redirect('/followers')


##############################################################################
# END FOLLOWERS/FRIENDS ROUTES 
##############################################################################


##############################################################################
# BEGIN SEARCH ROUTES 
##############################################################################

# displaying the search
@app.route('/search', methods=['GET'])
def search_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    form = SearchForm(request.args)
    
    if request.args.get('search'):
        
        # defining empty variables
        beers = None
        breweries = None
        styles = None

        # searching each possible source
        if (request.args.get('searchfor') == 'Beer' or request.args.get('searchfor') == 'ALL'):
            beers = Beer.query.filter(Beer.name.ilike(f"%{request.args.get('search')}%")).order_by(Beer.name.asc()).all()
        if (request.args.get('searchfor') == 'Brewery' or request.args.get('searchfor') == 'ALL'):
            breweries = Brewery.query.filter(Brewery.name.ilike(f"%{request.args.get('search')}%")).order_by(Brewery.name.asc()).all()
        if (request.args.get('searchfor') == 'Style' or request.args.get('searchfor') == 'ALL'):
            styles = Style.query.filter(Style.style_name.ilike(f"%{request.args.get('search')}%")).order_by(Style.style_name.asc()).all()

        if beers == None and breweries == None and styles == None:
            flash("Sorry... no matches to that search. Please try another search.", 'danger')

        return render_template('search/index.html', form=form, beers=beers, breweries=breweries, styles=styles)

    else:
        return render_template('search/index.html', form=form)

# show beers from a particular brewery
@app.route('/search/brewery/<int:brewery_id>', methods=['GET'])
def brewery_beers(brewery_id):
    
    brewery = Brewery.query.get_or_404(brewery_id)
    beers = Beer.query.filter(Beer.brewery_id == brewery_id).order_by(Beer.name.asc()).all()

    return render_template('search/brewery.html', beers=beers, brewery=brewery)

# show beers from a particular style
@app.route('/search/style/<int:style_id>', methods=['GET'])
def style_beers(style_id):
    
    style = Style.query.get_or_404(style_id)
    beers = Beer.query.filter(Beer.style_id == style_id).order_by(Beer.name.asc()).all()

    return render_template('search/style.html', beers=beers, style=style)

##############################################################################
# END SEARCH ROUTES 
##############################################################################


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
    if form.validate_on_submit():

        # uploading the image to AWS
        filename = None
        img = request.files['image_url']
        if img:
                filename = secure_filename(img.filename)
                img.save(filename)
                content_type = mimetypes.guess_type(filename)[0]
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = 'checkin/' + filename,
                    ExtraArgs={'ACL': 'public-read', 'ContentType': content_type}
                )
                os.remove(filename)

        try:
            checkin = Checkin.add(
                user_id=session[CURR_USER_KEY],
                beer_id=beer.id,
                brewery_id = beer.brewery_id,
                style_id = beer.style_id,
                comments = form.comments.data,
                serving_size = form.serving_size.data,
                purchase_location = form.purchase_location.data,
                rating = form.rating.data,
                image_url = filename,
            )
            db.session.commit()

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            message = Markup("Error capturing the checkin addition. Please try again.")
            flash(message, 'danger')
            return render_template('/beer/checkin/<int:beer_id>', beer=beer, form=form)
        
        if checkin:
            flash(f"Your checkin for {beer.name} was added!", "success")
            return redirect('/profile/checkins')
    
    return render_template('beer/checkin.html', beer=beer, form=form)

@app.route('/beer/wishlist/add/<int:beer_id>', methods=['GET'])
def wishlist_add_beer(beer_id):
    
    beer = Beer.query.get_or_404(beer_id)

    try:
        wishlist = Wishlist.add(
            user_id=session[CURR_USER_KEY],
            beer_id=beer_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        message = Markup("Error capturing the wishlist addition. Is it already on your <a href=\"/profile/wishlist\">wishlist</a>?")
        flash(message, 'danger')
        return redirect(request.referrer)
    
    if wishlist:
        session[USER_WISHLIST].append(beer_id)
        flash(f"{beer.name} added to your wishlist", "success")

    return redirect(request.referrer)

@app.route('/beer/wishlist/delete/<int:beer_id>', methods=['GET'])
def wishlist_delete_beer(beer_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    beer = Beer.query.get_or_404(beer_id)

    try:
        wishlist = Wishlist.delete(
            user_id=session[CURR_USER_KEY],
            beer_id=beer_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error deleting this wishlist item from the database. Please try again.", 'danger')
        return redirect(request.referrer)

    flash(f"{beer.name} deleted from your wishlist", "success")
    return redirect(request.referrer)

##############################################################################
# END BEER/BREWERY/STYLE CHECKIN AND WISHLIST ROUTES 
##############################################################################


##############################################################################
# BEGIN PROFILE ROUTES 
##############################################################################

# displaying the profile
@app.route('/profile')
def profile_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    profile = User.query.get_or_404(session[CURR_USER_KEY])

    return render_template('profile/index.html', profile=profile)

# profile checkins
@app.route('/profile/checkins')
def mycheckins_page():
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    # pulling beer IDs for recent checkins
    activity_beers = (Checkin.query
                .filter(Checkin.user_id==session[CURR_USER_KEY], Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.beer_id)
                .all())
    activity_beer_ids = [id for id, in activity_beers]
    
    q_string = ''
    for beer_id in activity_beer_ids:
        q_string += "&ids="
        q_string += beer_id.__str__()

    res = requests.get(f"{BASE_API_URL}/beers?{q_string}")
    data = res.content
    data_array = json.loads(data)

    beers = {}

    for beer in data_array['beers']:

        beers[beer['id']] = {
            'beer_id': beer['id'],
            'name': beer['name'],
            'brewery': beer['brewery'],
            'style': beer['style'],
            'abv': beer['abv'],
            'descript': beer['descript']
        }

    # creating an list of checkin ids to create tuples of toasts and comments
    checkins = (Checkin.query
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .with_entities(Checkin.checkin_id)
                .all())
    checkin_ids = [id for id, in checkins]
    
    # creating tuple of toasts
    checkin_toasts = [toasts.serialize() for toasts in CheckinToast.query.filter(CheckinToast.checkin_id.in_(checkin_ids)).all()]
    toasts= {}
    for toast in checkin_toasts:
        toasts[toast['checkin_id']] = toasts.get(toast['checkin_id'], ()) + ({
            'user_id': toast['user_id'],
            'username': toast['username']
        },)

    # creating tuple of comments
    checkin_comments = [comments.serialize() for comments in CheckinComment.query.filter(CheckinComment.checkin_id.in_(checkin_ids)).all()]
    comments= {}
    for comment in checkin_comments:
        comments[comment['checkin_id']] = comments.get(comment['checkin_id'], ()) + ({
            'user_id': comment['user_id'],
            'username': comment['username'],
            'comments': comment['comments']
        },)

    # pulling recent checkins
    ratings = (Checkin.query
                .filter(Checkin.user_id==session[CURR_USER_KEY], Checkin.deleted_dt==None)
                .order_by(Checkin.created_dt.desc())
                .limit(100)
                .all())

    return render_template('profile/checkins.html', ratings=ratings, beers=beers, toasts=toasts, comments=comments)

# edit profile checkins
@app.route('/profile/checkin/edit/<int:checkin_id>', methods=['GET', 'POST'])
def edit_checkin_page(checkin_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    # pulling recent checkins
    checkin = Checkin.query.get_or_404(checkin_id)
    form = BeerCheckinForm(obj=checkin)
    beer = Beer.query.get_or_404(checkin.beer_id)

    if form.validate_on_submit():

        # uploading the image to AWS
        filename = checkin.image_url
        img = request.files['image_url']
        if img:
                filename = secure_filename(img.filename)
                img.save(filename)
                content_type = mimetypes.guess_type(filename)[0]
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = 'checkin/' + filename,
                    ExtraArgs={'ACL': 'public-read', 'ContentType': content_type}
                )
                os.remove(filename)

        try:
            checkin = Checkin.edit(
                checkin_id=checkin_id,
                comments=form.comments.data,
                serving_size=form.serving_size.data,
                purchase_location=form.purchase_location.data,
                rating=form.rating.data,
                image_url=filename,
            )

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            flash("Error saving to the database. Please try again.", 'danger')
            return render_template('/profile/edit.html')

        flash(f"Checkin updated!", "success")
        return redirect('/profile/checkins')

    else:
        return render_template('profile/edit_checkin.html', checkin=checkin, beer=beer, form=form)

# edit profile checkins
@app.route('/profile/checkin/delete/<int:checkin_id>', methods=['GET'])
def delete_checkin_page(checkin_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    try:
        checkin = Checkin.delete(
            checkin_id=checkin_id,
        )
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error saving to the database. Please try again.", 'danger')
        return redirect('/profile/checkins')

    flash(f"Checkin deleted!", "success")
    return redirect('/profile/checkins')

# displaying the profile following
@app.route('/profile/following')
def following_page():

    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")

    # pulling follow requests
    pending_followings = (UserConnection.query
                .filter(UserConnection.connector_user_id==session[CURR_USER_KEY], UserConnection.approved_dt == None)
                .order_by(UserConnection.created_dt.desc())
                .with_entities(UserConnection.connectee_user_id)
                .all())
    pending_followings_ids = [id for id, in pending_followings]
    
    pending_users = (User.query
            .filter(User.user_id.in_(pending_followings_ids))).all()
    
    # pulling follow requests
    approved_followings = (UserConnection.query
                .filter(UserConnection.connector_user_id==session[CURR_USER_KEY], UserConnection.approved_dt != None)
                .order_by(UserConnection.created_dt.desc())
                .with_entities(UserConnection.connectee_user_id)
                .all())
    approved_followings_ids = [id for id, in approved_followings]
    
    approved_users = (User.query
            .filter(User.user_id.in_(approved_followings_ids))).all()
    
    return render_template('profile/following.html', approved_users=approved_users, pending_users=pending_users)

@app.route('/profile/following/delete/<int:user_id>', methods=['GET'])
def delete_following(user_id):
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    try:
        db.session.query(UserConnection).filter(UserConnection.connector_user_id==session[CURR_USER_KEY], UserConnection.connectee_user_id==user_id).delete()
        db.session.commit()

    except IntegrityError as error:
        # flash(f"{error}", 'danger')
        flash("Error saving to the database. Please try again.", 'danger')
        return redirect('/profile/checkins')

    flash(f"Following request deleted!", "success")
    return redirect('/profile/following')

# displaying the profile wishlist
@app.route('/profile/wishlist', methods=['GET', 'POST'])
def profile_wishlist():
    
    # checking to see if the user has signed in
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/user/login")
    
    # pulling beer IDs for wishlist
    wishlist_beers = (Wishlist.query
                .filter(Wishlist.user_id == session[CURR_USER_KEY], Wishlist.deleted_dt == None)
                .order_by(Wishlist.created_dt.desc())
                .limit(100)
                .with_entities(Wishlist.beer_id)
                .all())
    wishlist_beer_ids = [id for id, in wishlist_beers]
    
    q_string = ''
    for beer_id in wishlist_beer_ids:
        q_string += "&ids="
        q_string += beer_id.__str__()

    res = requests.get(f"{BASE_API_URL}/beers?{q_string}")
    data = res.content
    data_array = json.loads(data)

    beers = {}

    for beer in data_array['beers']:

        beers[beer['id']] = {
            'beer_id': beer['id'],
            'name': beer['name'],
            'brewery': beer['brewery'],
            'style': beer['style'],
            'abv': beer['abv'],
            'descript': beer['descript']
        }

    wishlist = Wishlist.query.filter(Wishlist.user_id == session[CURR_USER_KEY], Wishlist.deleted_dt == None).order_by(Wishlist.created_dt.desc()).all()

    return render_template('/profile/wishlist.html', wishlist=wishlist, beers=beers)

# displaying the change password screens / functionality
@app.route('/profile/changepw', methods=['GET', 'POST'])
def change_pw():
    
    user = User.query.get_or_404(session[CURR_USER_KEY])
    form = ChangePWForm()

    if form.validate_on_submit():
        
        # Checking that the new PWs match
        if form.new_password.data != form.new_password_confirm.data:
            flash("Sorry... those new passwords do not match. Please try again.", 'danger')
            return render_template('/profile/changepw.html', form=form)
        
        # Checking that the Current PW is correct
        if bcrypt.check_password_hash(user.password,form.current_password.data) == False:
            flash("Sorry... that is not the correct password. Please try again.", 'danger')
            return render_template('/profile/changepw.html', form=form)

        try:
            user = User.changepw(
                user_id=session[CURR_USER_KEY],
                password=form.new_password.data,
            )

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            flash("Error saving to the database. Please try again.", 'danger')
            return render_template('/profile/changepw.html', form=form)

        flash(f"Password updated!", "success")
        return redirect('/profile')

    else:
        return render_template('/profile/changepw.html', form=form)

# edit profile screens / functionality
@app.route('/profile/edit', methods=['GET', 'POST'])
def profile_edit():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    profile = User.query.get_or_404(session[CURR_USER_KEY])
    form = EditProfileForm(obj=profile)

    if form.validate_on_submit():
        
        # uploading the image to AWS
        filename = profile.image_url
        img = request.files['image_url']
        if img:
                filename = secure_filename(img.filename)
                img.save(filename)
                content_type = mimetypes.guess_type(filename)[0]
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = 'profile/' + filename,
                    ExtraArgs={'ACL': 'public-read', 'ContentType': content_type}
                )
                os.remove(filename)
        
        try:
            profile = User.edit(
                user_id=session[CURR_USER_KEY],
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                location=form.location.data,
                bio=form.bio.data,
                image_url=filename,
            )

        except IntegrityError as error:
            # flash(f"{error}", 'danger')
            flash("Error saving to the database. Please try again.", 'danger')
            return render_template('/profile/edit.html')

        flash(f"Profile updated!", "success")
        return redirect('/profile')

    else:
        return render_template('/profile/edit.html', form=form)


##############################################################################
# END PROFILE ROUTES 
##############################################################################

# BEGIN API ROUTES
@app.route('/api/beer/showall')
def api_beer_showall():
    beers = Beer.query.order_by(Beer.name.asc()).all()
    return render_template('api/beers/index.html', beers=beers)

@app.route('/api/beer/search', methods=['GET', 'POST'])
def api_beer_search_by_string():

    search = request.form.get('search')
    beer_results = [beers.serialize() for beers in Beer.query.filter(Beer.name.ilike(f"%{search}%")).order_by(Beer.name.asc()).all()]
    flash(f"beer_results: {beer_results}", "success")
    return render_template('api/beers/index.html')
    #return jsonify(beers=beer_results)

@app.route('/api/beer/<int:beer_id>', methods=['GET', 'POST'])
def api_beer_by_id(beer_id):
    beer = Beer.query.get_or_404(beer_id)
    beer_results = [beer.serialize()]
    return jsonify(beers=beer_results)
    
@app.route('/api/beers', methods=['GET', 'POST'])
def api_beers_by_ids():
    ids = request.args.getlist('ids', type=int)
    # ids = [5737,3985,8]
    # http://127.0.0.1:5000/api/beers?ids=5737&ids=3985&ids=8&ids=304&ids=316
    beer_results = [beers.serialize() for beers in Beer.query.filter(Beer.id.in_(ids)).all()]
    return jsonify(beers=beer_results)

@app.route('/api/brewery/showall')
def api_brewery_showall():
    breweries = Brewery.query.order_by(Brewery.name.asc()).all()
    return render_template('api/breweries/index.html', breweries=breweries)

@app.route('/api/brewery/search', methods=['GET', 'POST'])
def api_brewery_search_by_string():

    search = request.form.get('search')
    brewery_results = [breweries.serialize() for breweries in Brewery.query.filter(Brewery.name.ilike(f"%{search}%")).order_by(Brewery.name.asc()).all()]
    return jsonify(breweries=brewery_results)

@app.route('/api/style/showall')
def api_style_showall():
    styles = Style.query.order_by(Style.style_name.asc()).all()
    return render_template('api/styles/index.html', styles=styles)

@app.route('/api/style/search', methods=['GET', 'POST'])
def api_syle_search_by_string():

    search = request.form.get('search')
    style_results = [styles.serialize() for styles in Style.query.filter(Style.style_name.ilike(f"%{search}%")).order_by(Style.style_name.asc()).all()]
    return jsonify(styles=style_results)

# END API ROUTES
