from flask import Blueprint, render_template, flash, request, redirect, url_for
from flask.ext.login import login_user, logout_user, login_required
from flask.ext.sqlalchemy import SQLAlchemy
from silverflask import cache
from silverflask.forms import LoginForm
from silverflask.models import db, User, SiteTree
from flask import jsonify

main = Blueprint('main', __name__)

@main.route('/')
@cache.cached(timeout=1000)
def home():
    s = SiteTree()
    db.session.add(s)
    s.name = "Test!"
    s.parent_id = None
    db.session.commit()
    st = SiteTree.get_sitetree()
    print(st)

    return s.get_cms_form()
    return render_template('index.html')


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # For demonstration purposes the password in stored insecurely
        user = User.query.filter_by(username=form.username.data,
                                    password=form.password.data).first()

        if user:
            login_user(user)

            flash("Logged in successfully.", "success")
            return redirect(request.args.get("next") or url_for(".home"))
        else:
            flash("Login failed.", "danger")

    return render_template("login.html", form=form)


@main.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for(".home"))


@main.route("/restricted")
@login_required
def restricted():
    return "You can only see this if you are logged in!", 200

@main.route("/data")
def data():
    ss = SiteTree.query.limit(100)
    data = [s.as_dict() for s in ss]
    return jsonify(data=data)