import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import io
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.ndimage import rotate
from PIL import Image

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def current_weather(latitude,longitude):
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "cloud_cover", "wind_speed_10m","snow_depth"]
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    # Current values. The order of variables needs to be the same as requested.
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_cloud_cover = current.Variables(1).Value()
    current_wind_speed_10m = current.Variables(2).Value()
    snow_depth=current.Variables(3).Value()
    return current_temperature_2m, current_cloud_cover, current_wind_speed_10m, snow_depth

def forecast_3days(latitude,longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "snowfall", "snow_depth", "precipitation_probability", "rain", "cloud_cover", "visibility", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": 3
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(1).ValuesAsNumpy()
    hourly_snow_depth = hourly.Variables(2).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(3).ValuesAsNumpy()
    hourly_rain = hourly.Variables(4).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(5).ValuesAsNumpy()
    hourly_visibility = hourly.Variables(6).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(7).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(8).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "temperature_2m": hourly_temperature_2m, "snowfall": hourly_snowfall, "snow_depth": hourly_snow_depth,
        "precipitation_probability": hourly_precipitation_probability, "rain": hourly_rain,
        "cloud_cover": hourly_cloud_cover, "visibility": hourly_visibility, "wind_speed_10m": hourly_wind_speed_10m,
        "wind_direction_10m": hourly_wind_direction_10m}

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    return hourly_dataframe

def get_forecast_plots(latitude, longitude):
    forecast = forecast_3days(latitude, longitude)

    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 6), sharex=True)

    # Wykres temperatury
    ax1.plot(forecast['date'], forecast['temperature_2m'], label='Temperatura (°C)', color='tab:red')
    ax1.set_ylabel('Temperatura (°C)')
    ax1.set_title('Temperatura')
    ax1.legend()
    ax1.grid(True)

    # Wykres opadów
    ax2.plot(forecast['date'], forecast['rain'], label='Opady deszczu (mm)', color='mediumblue')
    ax2.plot(forecast['date'], forecast['snowfall'], label='Opady śniegu (mm)', color='lightskyblue')

    ax2.set_ylabel('Opady (mm)')
    ax2.set_title('Opady')
    ax2.legend(loc='upper left')
    ax2.grid(True)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=3))

    ax3 = ax2.twinx()  #osobna skala dla prawdopodobienstwa opadów
    ax3.fill_between(forecast['date'], 0, forecast['precipitation_probability'], color='lightslategray', alpha=0.2,
                     label='Prawd. opadów')
    ax3.set_ylabel('Prawd. opadów (%)')
    ax3.set_ylim(0, 100)
    ax3.legend(loc='upper right')

    fig.autofmt_xdate() # automatyczne obracanie etykiet

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    # Konwersja wykresu do formatu base64, aby można go było wyświetlić w HTML
    img_b64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return img_b64


def wind_plot(latitude, longitude):
    forecast=forecast_3days(latitude, longitude)

    img = Image.open("static/pngegg.png")
    img = img.convert("RGBA")
    arrow_img = np.array(img)

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
    fig.autofmt_xdate()

    dates = forecast['date']
    wind_speed = forecast['wind_speed_10m']
    wind_direction = forecast['wind_direction_10m']

    ax.plot(forecast["date"], forecast["wind_speed_10m"], color="green")
    ax.set_ylabel('Prędkość wiatru (km/h)')
    ax.set_title('Prędkość i kierunek wiatru')
    ax.legend()
    ax.grid(True)

    # Dodanie strzałek
    for i in range(0, len(dates),len(dates)//24):
        img_rotated = rotate(arrow_img, angle=-wind_direction[i], reshape=True)

        imagebox = OffsetImage(img_rotated, zoom=0.025)
        ab = AnnotationBbox(imagebox, (dates[i], wind_speed[i]), frameon=False)
        ax.add_artist(ab)

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    img_b64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return img_b64

