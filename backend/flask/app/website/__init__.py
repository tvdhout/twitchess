from flask import Blueprint, render_template

website_blueprint = Blueprint('website', __name__, template_folder='templates', static_folder='static')


@website_blueprint.route('/')
def index():
    return render_template("homepage.html")


@website_blueprint.route('/setup')
def setup():
    return render_template("setup.html")


@website_blueprint.route('/not-eligible')
def not_elibigle():
    return render_template("not-eligible.html")
