from flask import render_template, send_file, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user

from avalanche_danger import avalanche_png
from models import User
from __init__ import app, db, PNG_PATH, bcrypt, login_manager
from weather import current_weather
from weather_locations import locations


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    t, cc, w, sd = current_weather(49.2319, 19.9817)

    return render_template("index.html",
                           temperature=round(t),
                           cloud_cover=round(cc, 2),
                           wind=round(w, 2),
                           snow_depth=100 * round(sd, 4),
                           locations=locations)


@app.context_processor
def inject_locations():
    return {'locations': locations}


@app.route("/map")
def mapa():
    return render_template("map.html")

@app.route('/generate_png')
def generate_png():
    avalanche_png()
    return send_file(PNG_PATH, mimetype='image/png')


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash("Użytkownik już istnieje!", "danger")
            return redirect(url_for("register"))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Rejestracja zakończona sukcesem. Możesz się zalogować!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("Zalogowano pomyślnie!", "success")
            return redirect(url_for("home"))
        else:
            flash("Błędne dane logowania!", "danger")

    return render_template("login.html")


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Wylogowano!", "info")
    return redirect(url_for("home"))