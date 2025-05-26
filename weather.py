import datetime
import numpy as np
import openmeteo_requests
import requests_cache
from retry_requests import retry
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from scipy.ndimage import rotate
from PIL import Image
import os
import time
import threading
import locale
locale.setlocale(locale.LC_TIME, "polish")
lock = threading.Lock()

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

def forecast_5days(latitude,longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "snowfall", "snow_depth", "precipitation_probability", "rain", "cloud_cover", "visibility", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": 5
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]

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

def snow_depth_plot(forecast, latitude, longitude,historical):
    with lock:
        if not historical:
            snow_plot_filename = f"static/plots/snow_plot_{latitude}_{longitude}.png"
        else:
            snow_plot_filename= f"static/plots/historical_snow_plot_{latitude}_{longitude}.png"

        if os.path.exists(snow_plot_filename):
            last_modified_time = os.path.getmtime(snow_plot_filename)
            last_modified_hour = time.localtime(last_modified_time).tm_hour
            current_time = time.time()
            current_hour=time.localtime(current_time).tm_hour

            if current_hour == last_modified_hour:
                return snow_plot_filename

        fig, ax = plt.subplots(figsize=(16, 4))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        if historical:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        fig.autofmt_xdate()

        snow_depth = forecast['snow_depth'].apply(lambda x: 100*x)

        ax.fill_between(forecast["date"],0, snow_depth, color='lightskyblue',alpha=0.5)
        ax.set_ylabel('Pokrywa śnieżna (cm)')
        ax.set_title('Pokrywa śnieżna')
        ax.legend()
        ax.grid(True)

        plt.savefig(snow_plot_filename, format='png')
        plt.close()

        return snow_plot_filename


def get_forecast_plots(forecast, latitude, longitude,historical):
    with lock:
        if not historical:
            plot_filename = f"static/plots/forecast_temperature_plot_{latitude}_{longitude}.png"
        else:
            plot_filename = f"static/plots/historical_temperature_plot_{latitude}_{longitude}.png"

        if os.path.exists(plot_filename):
            last_modified_time = os.path.getmtime(plot_filename)
            last_modified_hour = time.localtime(last_modified_time).tm_hour
            current_time = time.time()
            current_hour=time.localtime(current_time).tm_hour

            if current_hour == last_modified_hour:
                return plot_filename

        fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(16, 6), sharex=True)
        ax1.set_title('Temperatura i opady')
        ax1.plot(forecast['date'], forecast['temperature_2m'], label='Temperatura (°C)', color='tab:red')
        ax1.set_ylabel('Temperatura (°C)')
        ax1.legend()
        ax1.grid(True)


        ax2.plot(forecast['date'], forecast['rain'], label='Opady deszczu (mm)', color='mediumblue')
        ax2.plot(forecast['date'], forecast['snowfall'], label='Opady śniegu (mm)', color='lightskyblue')
        ax2.set_ylabel('Opady (mm)')
        ax2.legend(loc='upper left')
        ax2.grid(True)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        if historical:
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
            ax2.xaxis.set_major_locator(mdates.DayLocator())

        if not historical:

            ax3 = ax2.twinx()  # osobna skala dla prawdopodobieństwa opadów
            ax3.fill_between(forecast['date'], 0, forecast['precipitation_probability'], color='lightslategray', alpha=0.2,
                             label='Prawdopodobieństwo opadów')
            ax3.set_ylabel('Prawd. opadów (%)')
            ax3.set_ylim(0, 100)
            ax3.legend(loc='upper right')

        fig.autofmt_xdate()

        fig.subplots_adjust(hspace=0)

        plt.savefig(plot_filename, format='png')
        plt.close()

        return plot_filename


def get_wind_plot(forecast, latitude, longitude,historical):
    with lock:
        if not historical:
            wind_plot_filename = f"static/plots/wind_plot_{latitude}_{longitude}.png"
        else:
            wind_plot_filename= f"static/plots/historical_wind_plot_{latitude}_{longitude}.png"
        img = Image.open("static/weather_icons/pngegg.png")
        img = img.convert("RGBA")
        arrow_img = np.array(img)

        if os.path.exists(wind_plot_filename):
            last_modified_time = os.path.getmtime(wind_plot_filename)
            last_modified_hour = time.localtime(last_modified_time).tm_hour
            current_time = time.time()
            current_hour=time.localtime(current_time).tm_hour

            if current_hour == last_modified_hour:
                return wind_plot_filename

        fig, ax = plt.subplots(figsize=(16, 4))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        if historical:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator())
        fig.autofmt_xdate()

        dates = forecast['date']
        wind_speed = forecast['wind_speed_10m']
        wind_direction = forecast['wind_direction_10m']


        ax.plot(forecast["date"], forecast["wind_speed_10m"], color="green")
        ax.set_ylabel('Prędkość wiatru (km/h)')
        ax.set_title('Prędkość i kierunek wiatru')
        ax.legend()
        ax.grid(True)

        for i in range(0, len(dates),len(dates)//24):
            if not np.isfinite(wind_direction[i]):
                continue
            img_rotated = rotate(arrow_img, angle=-wind_direction[i], reshape=True)
            imagebox = OffsetImage(img_rotated, zoom=0.025)
            ab = AnnotationBbox(imagebox, (dates[i], wind_speed[i]), frameon=False)
            ax.add_artist(ab)

        plt.savefig(wind_plot_filename, format='png')
        plt.close()

        return wind_plot_filename

def visibility_plot(forecast,latitude, longitude):
    with lock:
        visibility_plot_filename = f"static/plots/visibility_plot_{latitude}_{longitude}.png"


        if os.path.exists(visibility_plot_filename):
            last_modified_time = os.path.getmtime(visibility_plot_filename)
            last_modified_hour = time.localtime(last_modified_time).tm_hour
            current_time = time.time()
            current_hour=time.localtime(current_time).tm_hour

            if current_hour == last_modified_hour:
                return visibility_plot_filename

        fig, ax = plt.subplots(figsize=(16, 4))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
        fig.autofmt_xdate()

        dates = forecast['date']
        visibility = forecast['visibility']


        ax.plot(dates, visibility, color="pink")
        ax.set_ylabel('Widoczność (m)')
        ax.set_title('Widoczność')
        ax.legend()
        ax.grid(True)

        plt.savefig(visibility_plot_filename, format='png')
        plt.close()

        return visibility_plot_filename

def weather_icon(weather_code):
    if weather_code==0 or weather_code==1:
        return "/static/weather_icons/sunny.png"
    elif weather_code==2:
        return "/static/weather_icons/partly_cloudy.png"
    elif weather_code in (3,45,48):
        return "/static/weather_icons/cloudy.png"
    elif 51<=weather_code<=67 or 80<=weather_code<=82:
        return "/static/weather_icons/rainy.png"
    elif 71<=weather_code<=77 or weather_code==85 or weather_code==86:
        return "/static/weather_icons/snowy.png"
    elif 95<=weather_code<=99:
        return "/static/weather_icons/stormy.png"


def weather_table(latitude,longitude):
    def link_to_img(link):
        return f'<img src={link}>'

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["weather_code", "temperature_2m"],
        "temporal_resolution": "hourly_3",
        "forecast_days": 5
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_weather_code = hourly.Variables(0).ValuesAsNumpy()
    hourly_temperature_2m = hourly.Variables(1).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "weather_code": hourly_weather_code, "temperature_2m": hourly_temperature_2m}

    hourly_dataframe = pd.DataFrame(data=hourly_data )

    hourly_dataframe['weather_code'] = hourly_dataframe['weather_code'].apply(weather_icon).apply(link_to_img)
    hourly_dataframe['date']= hourly_dataframe['date'].apply(lambda x: x.strftime("%A %H:%M"))
    hourly_dataframe['temperature_2m'] = hourly_dataframe['temperature_2m'].apply(lambda x: str(round(x)) + "°C")
    hourly_dataframe=hourly_dataframe.transpose()
    html_table = hourly_dataframe.to_html(classes='table table-striped', index=False, escape=False,header=False)
    return html_table

def get_historical_weather(latitude,longitude):
    url = "https://archive-api.open-meteo.com/v1/archive"
    end_date = datetime.date.today()- datetime.timedelta(days=1)
    start_date = end_date - datetime.timedelta(days=14)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "hourly": ["temperature_2m", "rain", "snowfall", "snow_depth", "wind_speed_10m", "wind_direction_10m",
                   "direct_normal_irradiance", "shortwave_radiation"],
        "temporal_resolution": "hourly_6"
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()
    hourly_snowfall = hourly.Variables(2).ValuesAsNumpy()
    hourly_snow_depth = hourly.Variables(3).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(5).ValuesAsNumpy()
    hourly_direct_normal_irradiance = hourly.Variables(6).ValuesAsNumpy()
    hourly_shortwave_radiation = hourly.Variables(7).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "temperature_2m": hourly_temperature_2m, "rain": hourly_rain, "snowfall": hourly_snowfall,
        "snow_depth": hourly_snow_depth, "wind_speed_10m": hourly_wind_speed_10m,
        "wind_direction_10m": hourly_wind_direction_10m, "direct_normal_irradiance": hourly_direct_normal_irradiance,
        "shortwave_radiation": hourly_shortwave_radiation}

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    return hourly_dataframe