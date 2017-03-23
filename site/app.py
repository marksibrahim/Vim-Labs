"""
runs flask app
"""

from flask import Flask
from flask import render_template, request
import stripe
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

stripe_publishable_key = "pk_test_Wypi43lE9wNRG6zE8FC6Rbcz"

stripe.api_key = "sk_test_n1uEkuppBSnsH0pI3J6M17V0"


@app.route("/")
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

if __name__ == "__main__":
    app.run()
