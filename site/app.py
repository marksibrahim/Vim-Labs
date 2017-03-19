"""
runs flask app
"""

from flask import Flask
from flask import render_template
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True


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


if __name__ == "__main__":
    app.run()
