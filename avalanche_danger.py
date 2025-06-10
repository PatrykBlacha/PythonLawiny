import datetime
import os
import openmeteo_requests
import requests_cache
from PIL import Image
from retry_requests import retry
import pandas as pd
import rasterio
import numpy as np
from weather import current_weather

PNG_PATH='static/risk_map.png'


cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
def danger_table(latitude,longitude):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ["temperature_2m_max", "rain_sum", "snowfall_sum", "wind_gusts_10m_max", "temperature_2m_min"],
        "hourly": "snow_depth",
        "timezone": "auto",
        "past_days": 5,
        "forecast_days": 6
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]

    hourly = response.Hourly()
    hourly_snow_depth = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "snow_depth": hourly_snow_depth}


    hourly_dataframe = pd.DataFrame(data=hourly_data)
    hourly_dataframe['day'] = hourly_dataframe['date'].dt.date
    daily_max_snow = hourly_dataframe.groupby('day')['snow_depth'].max().reset_index()

    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(1).ValuesAsNumpy()
    daily_snowfall_sum = daily.Variables(2).ValuesAsNumpy()
    daily_wind_gusts_10m_max = daily.Variables(3).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(4).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ), "temperature_2m_max": daily_temperature_2m_max, "rain_sum": daily_rain_sum, "snowfall_sum": daily_snowfall_sum,
        "wind_gusts_10m_max": daily_wind_gusts_10m_max, "temperature_2m_min": daily_temperature_2m_min}


    daily_dataframe = pd.DataFrame(data=daily_data)

    icons=['<img src="/static/avalanche_icons/szare_kolko.png">' for _ in range(len(daily_dataframe))]
    for idx in range(len(daily_dataframe)):
        text = ''
        snow_today = daily_max_snow[daily_max_snow['day'] == daily_dataframe['date'][idx].date()]
        if not snow_today.empty:
            snow_depth_today = snow_today['snow_depth'].values[0]
            if snow_depth_today==0:
                continue
        else:
            continue

        days_min=0
        days_max=0
        if daily_wind_gusts_10m_max[idx]>40:
            conditions=2
            text = 'silny wiatr'
            days_min=2
            days_max=4
        if daily_temperature_2m_max[idx] < -8:
            conditions=2
            if text:
                text+=', niska temperatura'
            else:
                text='niska temperatura'
        if daily_wind_gusts_10m_max[idx]<25 and daily_temperature_2m_max[idx]<0 and daily_temperature_2m_min[idx]>-10:
            conditions=0
        else:
            conditions=1
        if conditions==2 and daily_snowfall_sum[idx]>=15 or conditions==1 and daily_snowfall_sum[idx]>=25 or conditions==0 and daily_snowfall_sum[idx]>=40:
            if text:
                text+=', duże opady śniegu'
            else:
                text='duże opady śniegu'
            if not days_min:
                days_min, days_max=1,3
        if daily_temperature_2m_max[idx]-daily_temperature_2m_min[idx]>10:
            if not days_min:
                days_min, days_max = 1, 3
            if not text:
                text='duży wzrost temperatury'
            else: text+=', duży wzrost temperatury'

        if daily_rain_sum[idx]>10 and snow_depth_today>0:
            if not days_min:
                days_min, days_max = 1, 2
            if not text:
                text='deszcz na śnieg'
            else: text+=', deszcz na śnieg'
        if text:
            icons[idx]=f'<img src="/static/avalanche_icons/achtung.png" title="{text}">'
            for i in range(idx+1,min(idx+days_min+1,len(daily_dataframe))):
                icons[i] = f'<img src="/static/avalanche_icons/pomaranczowe_kolko.png" title="{text}">'
            for i in range(idx+days_min+1,min(idx+days_max+1,len(daily_dataframe))):
                icons[i] = f'<img src="/static/avalanche_icons/zolte_kolko.png" title="{text}">'


    daily_dataframe['icon'] = icons
    table_data = daily_dataframe[['date', 'icon']][daily_dataframe['date'].dt.date>=datetime.date.today()]
    table_data['date'] = table_data['date'].apply(lambda x: x.strftime("%d-%m"))
    table_data=table_data.transpose()
    html_table = table_data.to_html(classes='table table-striped',index=False, escape=False, header=False)

    today_icon = daily_dataframe.loc[
        daily_dataframe['date'].dt.date == datetime.date.today(), 'icon'
    ].values

    add_to_risk = 0
    if len(today_icon) > 0:
        if "achtung.png" in today_icon[0] or "pomaranczowe_kolko.png" in today_icon[0]:
            add_to_risk += 2
        elif "zolte_kolko.png" in today_icon[0]:
            add_to_risk += 1

    return html_table,add_to_risk


TOPR_URL = "https://lawiny.topr.pl"
def get_avalanche_risk_topr():
    # wyznaczone na podstawie grubosci pokrywy snieznej na kasprowym wierchu i czynników zwiększających zagrożenie
    # nie jest to żaden użyteczny wzór,
    # jest użyty tylko w celu zasymulowania danych, które docelowo powinny być udostępniane przez topr
    _,_,_,snow_depth = current_weather(49.2319,19.9817)
    _,add=danger_table(49.2319,19.9817)
    if snow_depth>150:
        return 3 + add
    elif snow_depth>80:
        return 2 + add
    elif snow_depth>50:
        return 1+add
    elif snow_depth>30:
        return 1 + add//2
    else:
        return 0

def is_snow_wet():
    # moznaby uwzglednic wysokosc npm
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 49.2319,
        "longitude": 19.9817,
        "daily": ["temperature_2m_max", "rain_sum"],
        "timezone": "auto",
        "forecast_days": 1
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(1).ValuesAsNumpy()
    if daily_rain_sum>3 or daily_temperature_2m_max>0:
        return True
    return False

def generate_risk_map():
    with rasterio.open('static/NMT_tatry2.tif') as dem:
        dem_data = dem.read(1).astype(np.float32)
        transform = dem.transform

        res_x = abs(transform.a)
        res_y = abs(transform.e)

        lat_deg = 49.5
        lat_rad = np.radians(lat_deg)

        meters_per_degree_lat = 111_320
        meters_per_degree_lon = 111_320 * np.cos(lat_rad)

        res_x_meters = res_x * meters_per_degree_lon
        res_y_meters = res_y * meters_per_degree_lat

        dzdx = np.gradient(dem_data, axis=1) / res_x_meters
        # pochodne obliczone metoda ilorazow roznicowych, na brzegach pochodne jednostronne,
        # w pozostalych punktach obustronne
        dzdy = np.gradient(dem_data, axis=0) / res_y_meters
        slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))
        aspect = (90 - np.degrees(np.arctan2(dzdy, dzdx))) % 360

        risk_map = np.full_like(slope, 2**3)
        risk_map[(slope > 35) & (slope < 40)] /= 2
        risk_map[(slope > 30) & (slope < 35)] /= 3
        risk_map[(slope < 30)] /= 4

        if not is_snow_wet():
            risk_map[((aspect > 45) & (aspect < 67.5)) | ((aspect > 292.5) & (aspect < 315))] /= 2
            risk_map[(aspect > 67.5) & (aspect < 292.5)] /= 3

        # risk map mozna wykorzystac do szukania optymalnej trasy
        return risk_map
def avalanche_png():
    if os.path.exists(PNG_PATH):
        last_modified_time = os.path.getmtime(PNG_PATH)
        last_mod_date = datetime.datetime.fromtimestamp(last_modified_time).date()
        current_date = datetime.datetime.now().date()

        if last_mod_date == current_date:
            return
    risk_map=generate_risk_map()


    img = Image.new('RGBA', (risk_map.shape[1], risk_map.shape[0]))
    colormap = {
        1: (0, 255, 0, 100),    # green low
        2: (255, 165, 0, 120),  # orange medium
        3: (255, 0, 0, 150),    # red high
    }

    for y in range(img.height):
        for x in range(img.width):
            val = risk_map[y, x]
            if val < 1.5:
                img.putpixel((x, y), colormap[1])
            elif val < 2.5:
                img.putpixel((x, y), colormap[2])
            else:
                img.putpixel((x, y), colormap[3])

    img.save(PNG_PATH)



# funkcja tylko do sprawdzenia w którym miejscu na mapie wyswietlić nakładkę lawinową
def get_bounds_from_dem(path):
    with rasterio.open(path) as src:
        bounds = src.bounds  # Zwraca (left, bottom, right, top)
        return [[bounds.top, bounds.left], [bounds.bottom, bounds.right]]
