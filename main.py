from routes import *

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Baza danych została zainicjalizowana.")
    print(weather_icon(1))
    print(get_avalanche_risk_topr())
    app.run(debug=True)
