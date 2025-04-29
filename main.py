import requests
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS

from weather import *
from weather_locations import locations

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'tajny_klucz'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
CORS(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    t, cc, w,sd = current_weather(49.2319,19.9817)
    return render_template("index.html",temperature=round(t,2),cloud_cover=round(cc,2),wind=round(w,2),snow_depth=100*round(sd,4),locations=locations)

@app.context_processor
def inject_locations():
    return {'locations': locations}

@app.route("/map")
def mapa():
    return render_template("map.html")


@app.route("/search_peak", methods=["GET"])
def search_peak():
    peak_name = request.args.get("q")

    if not peak_name:
        return jsonify({"error": "Brak nazwy szczytu"}), 400

    # Nominatium  OpenStreetMap API
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={peak_name}&featuretype=peak"
    headers = {"User-Agent": "Tu mozna wpisac doslownie dowolna rzecz i bedzie dzialac"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return jsonify({"error": "Błąd połączenia z Nominatim API"}), 500

    data = response.json()

    if not data:
        return jsonify({"error": "Nie znaleziono szczytu"}), 404

    result = {
        "name": peak_name,
        "lat": data[0]["lat"],
        "lon": data[0]["lon"]
    }

    return jsonify(result)

@app.route("/pogoda/<location>")
def weather(location):
    location = location.replace("_", " ")
    latitude,longitude=locations.get(location)
    forecast=forecast_3days(latitude,longitude)
    temperature=get_forecast_plots(latitude,longitude)
    wind=wind_plot(latitude,longitude)
    t, cc, w, sd = current_weather(latitude,longitude)

    return render_template("weather.html",temperature=round(t, 2), cloud_cover=round(cc, 2), wind=round(w, 2),
                           snow_depth=round(sd*100, 2),temperature_=temperature,wind_=wind,location=location,locations=locations,forecast=forecast,latitude=latitude,longitude=longitude)

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
def logout():
    logout_user()
    flash("Wylogowano!", "info")
    return redirect(url_for("home"))



if __name__ == "__main__":
    app.run(debug=True)
