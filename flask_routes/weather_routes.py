from flask import render_template

from __init__ import app
from avalanche_danger import danger_table
from weather import forecast_5days, current_weather, get_forecast_plots, visibility_plot, get_historical_weather, \
    get_wind_plot, snow_depth_plot, weather_table
from weather_locations import locations, cameras


@app.route("/pogoda/<location>")
def weather(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    t, cc, w, sd = current_weather(latitude, longitude)

    if location in cameras:
        camera_links = cameras[location]
    else:
        camera_links = []

    return render_template("weather.html", temperature=round(t), cloud_cover=round(cc, 2), wind=round(w, 2),
                           forecast=forecast,
                           snow_depth=round(sd * 100, 2), location=location, locations=locations, latitude=latitude,
                           longitude=longitude, cameras=camera_links)


@app.route("/api/temperature_plot/<location>")
def generate_temperature_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot = get_forecast_plots(forecast, latitude, longitude, False)
    return f'<img src="/{plot}" alt="Wykres temperatury" style="max-width: 100%;">'


@app.route("/api/visibility_plot/<location>")
def generate_visibility_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot = visibility_plot(forecast, latitude, longitude)
    return f'<img src="/{plot}" alt="Wykres widoczności" style="max-width: 100%;">'


@app.route("/api/historical_temperature_plot/<location>")
def generate_historical_temperature_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = get_historical_weather(latitude, longitude)
    plot = get_forecast_plots(forecast, latitude, longitude, True)
    return f'<img src="/{plot}" alt="Wykres temperatury" style="max-width: 100%;">'


@app.route("/api/historical_wind_plot/<location>")
def generate_historical_wind_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = get_historical_weather(latitude, longitude)
    plot = get_wind_plot(forecast, latitude, longitude, True)
    return f'<img src="/{plot}" alt="Wykres wiatru" style="max-width: 100%;">'


@app.route("/api/wind_plot/<location>")
def generate_wind_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot = get_wind_plot(forecast, latitude, longitude, False)
    return f'<img src="/{plot}" alt="Wykres wiatru" style="max-width: 100%;">'


@app.route("/api/historical_snow_plot/<location>")
def generate_historical_snow_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = get_historical_weather(latitude, longitude)
    plot = snow_depth_plot(forecast, latitude, longitude, True)
    return f'<img src="/{plot}" alt="pokrywa sniezna" style="max-width: 100%;">'


@app.route("/api/snow_plot/<location>")
def generate_snow_plot(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    forecast = forecast_5days(latitude, longitude)
    plot = snow_depth_plot(forecast, latitude, longitude, False)
    return f'<img src="/{plot}" alt="pokrywa sniezna" style="max-width: 100%;">'


@app.route("/api/forecast/<location>")
def generate_forecast(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    return weather_table(latitude, longitude)


@app.route("/api/danger/<location>")
def generate_danger(location):
    location = location.replace("_", " ")
    latitude, longitude = locations.get(location)
    return danger_table(latitude, longitude)