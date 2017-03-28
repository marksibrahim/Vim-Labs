"""
runs flask app
"""

import os
import stripe
from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user, login_required
from oauth import OAuthSignIn

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'google': {
        'id': '939082582563-8vivf9l29b3m1dqefam9cf64fhrdtus9.apps.googleusercontent.com',
        'secret': os.environ['G-SECRET']
    },
}


db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'login'

stripe_publishable_key = "pk_test_Wypi43lE9wNRG6zE8FC6Rbcz"
stripe.api_key = "sk_test_n1uEkuppBSnsH0pI3J6M17V0"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    # defaults to true; change this behavior once live
    paid = db.Column(db.Boolean)


@app.route('/')
@app.route("/landing.html/")
def landing():
    return render_template("landing.html")


@app.route('/modules/<number>')
def module(number):
    return render_template('module'+ number +'.html')


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
    return render_template('charge.html', key=stripe_publishable_key)


@app.route('/paid', methods=['POST'])
@login_required
def paid():
    # Amount in cents
    amount = 500
    customer = stripe.Customer.create(
        email='customer@example.com',
        source=request.form['stripeToken']
    )
    charge = stripe.Charge.create(
        customer=customer.id,
        amount=amount,
        currency='usd',
        description='Flask Charge'
    )
    # mark user as paid
    current_user.paid = True
    db.session.add(current_user)
    db.session.commit()
    return render_template('paid.html', amount=amount)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))

@app.route('/login')
def login():
    return render_template('login.html')

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

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
