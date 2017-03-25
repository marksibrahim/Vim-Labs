"""
runs flask app
TODO
try using
https://github.com/lepture/flask-oauthlib/blob/master/example/google.py
and protecting views using
http://stackoverflow.com/questions/9499286/using-google-oauth2-with-flask
"""

import stripe
from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from oauth import OAuthSignIn

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'google': {
        'id': '939082582563-i176fv0cjuta33p5r9g57v1kvmmu94be.apps.googleusercontent.com',
        'secret': 'u-_wfneVvcOpjX_iP5yR3GFS'
    },
}


db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'landing'

stripe_publishable_key = "pk_test_Wypi43lE9wNRG6zE8FC6Rbcz"
stripe.api_key = "sk_test_n1uEkuppBSnsH0pI3J6M17V0"

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)

@app.route('/')
@app.route("/landing.html/")
def landing():
    return render_template("landing.html")

@app.route('/modules/<number>')
def module(number):
    return render_template('module'+ number +'.html')

@app.route('/premium/<number>')
def private_module(number):
    print("private")
    return render_template('p_module' + number)


@app.route('/charge')
def charge():
    return render_template('charge.html', key=stripe_publishable_key)

@app.route('/paid', methods=['POST'])
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

    return render_template('paid.html', amount=amount)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('landing'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('landing'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('landing'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('landing'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('landing'))

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
