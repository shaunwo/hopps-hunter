# Hopps Hunter Proposal
by Shaun Worcester

## Objective
A fun site to search for, check-in, rate and interact with others about you favorite beers in your local area, or across the globe. Craft beer is a passion of mine, and I know that local breweries continue to enjoy a revival in the USA in recent years. I personally use Untappd on a regular basis, and I am planning to mimic some of the functionality of the app, and improve in some other areas.

## Audience
In my experience, craft beer aficionados are largely men, but not only. I think the interest is targeted at both genders, and anyone 21 and up. Anyone who loves beer and cares to talk about it is welcome!

## Data Source
API: [https://untappd.com/api/docs](https://untappd.com/api/docs)

APP DB: PostgreSQL

I will pull most of the beer and brewery info from the Untappd API, but the user accounts, check-ins, follows and other interactions will be stored in the PostgreSQL DB that I will build.

## Approach
### Database Schema
At the outset, I will need at least the following DB tables in ProgreSQL for what I will build:

![Hopps Hunter DB Schema.png](https://github.com/shaunwo/hopps-hunter/blob/207bd4ea02840511cf70f066ed12c94463ab30d4/Hopps%20Hunter%20DB%20Schema.png)

### Sensitive Information

* Usernames and Passwords
	* Passwords will be stored with Flask Bcrypt
* Check-ins, follows, and other features of a User’s profile if they choose to keep their account private

### Functionality
An interactive community for craft beer lovers where users can connect with one another, follow their favorite brews, and look for new ones.

### User Flow
![Hopps Hunter User Flow Diagram.png](https://github.com/shaunwo/hopps-hunter/blob/1fccde36b2fa77caf968fae868e72ec9ecaa11c6/Hopps%20Hunter%20User%20Flow%20Diagram.png)

Users will create an account and log back into the system, and land on a page the display recent checkins from Untappd. A user will have the option to search by brewery, beer and/or style, and then check-in, rate, upload an image, or add an item to his/her wishlist. The user will see some alerts when they first sign in if there are any items on their wishlist that are now available in their area. The user can look at connected/”friended” users accounts and leave comments and toasts as well.

### Features
* A beautiful, clean interface that some may like better than Untappd
* Options to find top-ranked beers by style, across the globe, or in a user’s local area
* Sharing check-in / comments / details of a beer across the user’s favorite social media channels
* Alerts when a beer on a users wishlist becomes available at a local retailer

#### Stretch Goals
* Login with Facebook, Google, etc.
* Set up “subscriptions” for a beer from multiple zip codes
* Set up emails alerts where a user would received an e-mail when a beer is newly available in his/her area
* Option to look for possible friends through a user’s social media sites and/or address book

### Possible Issues
* At the moment, I am making a couple assumptions about what specific pieces of data are/are not available through the API. If some of those items are not available 
* Making something that is different enough from Untappd to not just be a clone
