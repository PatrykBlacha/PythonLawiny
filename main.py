from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import requests

# Import pogody
from weather import *
from weather_locations import locations

# Inicjalizacja aplikacji
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'tajny klucz'


db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
CORS(app)

#ogólniue kod do fragmentaryzacji ale to nigdy nie działało jak probowalem
#to mogloby byc w models.py
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    markers = db.relationship('Marker', backref='user', lazy=True)
    routes = db.relationship('Route', backref='user', lazy=True)


class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)


class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    waypoints = db.Column(db.Text, nullable=False)  # JSON string


#załadowanie użytkownika z usermanagera
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#ROUTY
#znowu fragmentaryzacja tu powinna wejsc

@app.route('/api/markers', methods=['POST'])
@login_required
def add_marker():
    #można sie pochwalic obsluga wyjatkow
    try:
        data = request.json
        new_marker = Marker(
            user_id=current_user.id,
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            description=data.get('description', '')
        )
        db.session.add(new_marker)
        db.session.commit()
        return jsonify({'message': 'Marker added successfully', 'id': new_marker.id}), 201
    except Exception as e:
        db.session.rollback()
        print("Error adding marker:", str(e))  # zobaczysz ten błąd w konsoli serwera
        return jsonify({'error': 'Server error: ' + str(e)}), 500

@app.route('/api/routes', methods=['POST'])
@login_required
def add_route():
    #tu tez moznaby dodac obsluge wyjatkow, jest juz w js ale lepiej miec kod w pythonie
    data = request.get_json()
    new_route = Route(
        user_id=current_user.id,
        name=data['name'],
        description=data.get('description', ''),
        waypoints=data['waypoints']  # to jest string JSONowy
    )
    db.session.add(new_route)
    db.session.commit()
    return jsonify({'message': 'Route added successfully'}), 201


@app.route('/api/routes/<int:route_id>', methods=['DELETE'])
@login_required
def delete_route(route_id):
    route = Route.query.get(route_id)
    if not route or route.user_id != current_user.id:
        return jsonify({'error': 'Brak dostępu lub trasa nie istnieje'}), 404

    db.session.delete(route)
    db.session.commit()
    return jsonify({'message': 'Trasa usunięta'})

#tu sa nudne zapytania do bazy
@app.route('/api/markers', methods=['GET'])
@login_required
def get_markers():
    markers = Marker.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': marker.id,
        'name': marker.name,
        'latitude': marker.latitude,
        'longitude': marker.longitude,
        'description': marker.description
    } for marker in markers])

@app.route('/api/routes', methods=['GET'])
@login_required
def get_routes():
    routes = Route.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': route.id,
        'name': route.name,
        'description': route.description,
        'waypoints': route.waypoints
    } for route in routes])

@app.route('/api/markers/<int:marker_id>', methods=['DELETE'])
@login_required
def delete_marker(marker_id):
    marker = Marker.query.get(marker_id)
    if not marker or marker.user_id != current_user.id:
        return jsonify({'error': 'Marker not found or unauthorized'}), 404
    db.session.delete(marker)
    db.session.commit()
    return jsonify({'message': 'Marker deleted successfully'})


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    t, cc, w,sd = current_weather(49.2319,19.9817)
    return render_template("index.html",temperature=round(t),cloud_cover=round(cc,2),wind=round(w,2),snow_depth=100*round(sd,4),locations=locations)

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
    forecast=forecast_5days(latitude,longitude)
    t, cc, w, sd = current_weather(latitude,longitude)

    return render_template("weather.html",temperature=round(t), cloud_cover=round(cc, 2), wind=round(w, 2), forecast=forecast,
                           snow_depth=round(sd*100, 2),location=location,locations=locations,latitude=latitude,longitude=longitude)

@app.route("/api/temperature_plot/<location>")
def generate_temperature_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast=forecast_5days(latitude,longitude)
    plot= get_forecast_plots(forecast,latitude,longitude, False)
    return f'<img src="/{plot}" alt="Wykres temperatury" style="max-width: 100%;">'

@app.route("/api/visibility_plot/<location>")
def generate_visibility_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast=forecast_5days(latitude,longitude)
    plot= visibility_plot(forecast,latitude,longitude)
    return f'<img src="/{plot}" alt="Wykres widoczności" style="max-width: 100%;">'
@app.route("/api/historical_temperature_plot/<location>")
def generate_historical_temperature_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast=get_historical_weather(latitude,longitude)
    plot= get_forecast_plots(forecast,latitude,longitude,True)
    return f'<img src="/{plot}" alt="Wykres temperatury" style="max-width: 100%;">'

@app.route("/api/historical_wind_plot/<location>")
def generate_historical_wind_plot(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    forecast = get_historical_weather(latitude, longitude)
    plot= get_wind_plot(forecast,latitude,longitude,True)
    return f'<img src="/{plot}" alt="Wykres wiatru" style="max-width: 100%;">'

@app.route("/api/wind_plot/<location>")
def generate_wind_plot(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot= get_wind_plot(forecast,latitude,longitude,False)
    return f'<img src="/{plot}" alt="Wykres wiatru" style="max-width: 100%;">'

@app.route("/api/historical_snow_plot/<location>")
def generate_historical_snow_plot(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    forecast = get_historical_weather(latitude, longitude)
    plot= snow_depth_plot(forecast,latitude,longitude,True)
    return f'<img src="/{plot}" alt="pokrywa sniezna" style="max-width: 100%;">'

@app.route("/api/snow_plot/<location>")
def generate_snow_plot(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot= snow_depth_plot(forecast,latitude,longitude,False)
    return f'<img src="/{plot}" alt="pokrywa sniezna" style="max-width: 100%;">'
@app.route("/api/forecast/<location>")
def generate_forecast(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    return weather_table(latitude,longitude)

@app.route("/api/danger/<location>")
def generate_danger(location):
    location = location.replace("_"," ")
    latitude, longitude = locations.get(location)
    return danger_table(latitude,longitude)

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



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Baza danych została zainicjalizowana.")
    print(weather_icon(1))
    app.run(debug=True)
