import os

from avalanche_danger import get_avalanche_risk_topr
from routes import get_routes_to_json
from flask_routes.map_routes import *
from flask_routes.weather_routes import *
from flask_routes.web_and_accounts_routes import *
from weather import weather_icon

PNG_PATH = 'static/risk_map.png'
if not os.path.exists("static/hiking_trails.geojson"):
    get_routes_to_json()




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Baza danych została zainicjalizowana.")
    print(weather_icon(1))
    print(get_avalanche_risk_topr())
    app.run(debug=True)