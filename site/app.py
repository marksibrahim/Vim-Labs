"""
Runs flask app
"""

import logging
import os
import stripe
from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user, login_required
from oauth import OAuthSignIn


app = Flask(__name__)
app.config['DEBUG'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = False
# secret key is used for encryption
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
# when running locally, you may to occassionaly update when secret is rotated
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ["DATABASE_URL"]
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['OAUTH_CREDENTIALS'] = {
    'google': {
        'id': '939082582563-8vivf9l29b3m1dqefam9cf64fhrdtus9.apps.googleusercontent.com',
        'secret': os.environ['G_SECRET']
    },
}


db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'

stripe_publishable_key = "pk_live_b02zbFTh4Gl4Mc6YTyQjtMgO"
stripe.api_key = os.environ["STRIPE_SECRET"]

# Uncomment for testing Stripe payments
# stripe_publishable_key = "pk_test_ZLPiXAZhOE09Nrc4p3AFe36C"
# stripe.api_key = "sk_test_j6Oc2z6SJ5yb6VnTzt0TRZPA"

# Vim Labs Pro
AMOUNT_CENTS = 500


class User(UserMixin, db.Model):
    """User class to determine premium users"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    paid = db.Column(db.Boolean, default=False)

    def __repr__(self):
        id_str = "ID: {}, social_id: {}".format(self.id, self.social_id)
        return "{} nickname: {}, email: {}, paid: {}".format(id_str, 
                                                              self.nickname,
                                                              self.email,
                                                              self.paid)


@app.route('/')
@app.route("/landing.html/")
def landing():
    return render_template("landing.html")


@app.route('/modules/<number>')
def module(number):
    return render_template('module'+ number +'.html')

@app.route('/practice/<number>')
def practice(number):
    return render_template('practice'+ number +'.html')

@app.route('/premium/<number>')
@login_required
def private_module(number):
    print("premium" + number)
    if not current_user.paid:
        redirect(url_for('charge'))
    return render_template('p_module' + number + '.html')


@app.route('/charge')
@login_required
def charge():
    """Page to accept Strip payment"""
    return render_template('charge.html',
                           key=stripe_publishable_key,
                           amount_dollars=int(AMOUNT_CENTS/100))


@app.route('/paid', methods=['POST'])
@login_required
def paid():
    """Accepts payment from charge.html and store premium user in DB"""
    # Token is created using Stripe.js or Checkout!
    # Get the payment token submitted by the form:
    token = request.form['stripeToken'] # Using Flask

    # Charge the user's card:
    charge = stripe.Charge.create(
      amount=AMOUNT_CENTS,
      currency="usd",
      description="Vim Labs Premium",
      source=token,
    )
    # mark user as paid
    current_user.paid = True
    db.session.add(current_user)
    db.session.commit()
    return render_template('login.html', pro=True)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('login'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('login'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('login'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email, paid=False)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    # if not paid, route to payment
    if not user.paid:
        print("redirecting to stripe charge")
        return redirect(url_for('charge'))
    return redirect(url_for('landing'))


@app.errorhandler(404)
def page_not_found(e):
    """log and return a pretty 404"""
    if current_user.is_anonymous:
        user_info = "anonymous user"
    else:
        user_info = str(current_user)

    logging.error("404 ERROR: {}".format(user_info))
    return render_template('404.html'), 404


@app.errorhandler(500)
def interal_server_error(e):
    """log and return a pretty 500"""
    if current_user.is_anonymous:
        user_info = "anonymous user"
    else:
        user_info = str(current_user)

    logging.error("500 ERROR: {}".format(user_info))
    return render_template('500.html')


if __name__ == "__main__":
    db.create_all()
    # development server
    app.config['DEBUG'] = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run()
