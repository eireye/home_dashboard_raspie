import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz
import pandas as pd
from lists.english_norwegian import weather_norwegian, norwegian_days
from lists.weather_emoji import weather_emoji
from utils.weather_api import get_weather

def show():
    st_autorefresh(interval=600000, key="weather_refresh")

    data = get_weather()
    oslo_tz = pytz.timezone('Europe/Oslo')
    now_oslo = datetime.now(oslo_tz)

    current_index = 0
    for i, timeseries in enumerate(data['properties']['timeseries']):
        forecast_time = datetime.fromisoformat(timeseries['time'].replace('Z', '+00:00'))
        if forecast_time >= now_oslo:
            current_index = i
            break

    current = data['properties']['timeseries'][current_index]
    temp_now = current['data']['instant']['details']['air_temperature']
    weather_symbol = current['data']['next_1_hours']['summary']['symbol_code']

    emoji = weather_emoji.get(weather_symbol, '🌡️')
    symbol_base = weather_symbol.replace('_day', '').replace('_night', '')
    norwegian_name = weather_norwegian.get(symbol_base, weather_symbol)

    # Compact header for 7" screen
    col_now, col_info = st.columns([1, 2])
    with col_now:
        st.metric(label="Nå", value=f"{temp_now}°C")
    with col_info:
        st.markdown(f"### {emoji} {norwegian_name}")

    # 12-hour chart (more compact for small screen)
    hours = []
    temps = []

    for i in range(current_index, min(current_index + 12, len(data['properties']['timeseries']))):
        hour_data = data['properties']['timeseries'][i]
        time_obj = datetime.fromisoformat(hour_data['time'].replace('Z', '+00:00'))
        time_oslo = time_obj.astimezone(oslo_tz)
        hour = time_oslo.strftime("%H")
        temp = hour_data['data']['instant']['details']['air_temperature']

        hours.append(hour)
        temps.append(temp)

    chart_data = pd.DataFrame({
        'Tid': hours,
        'Temp': temps
    })
    chart_data = chart_data.set_index('Tid')

    st.line_chart(chart_data, height=150)

    min_temp = min(temps)
    max_temp = max(temps)
    st.caption(f"↓ {min_temp}°C  |  ↑ {max_temp}°C")

    # 3-day forecast
    st.markdown("**Neste dager**")

    # Compact 3-day forecast in columns
    day_cols = st.columns(3)

    for idx, i in enumerate([24, 48, 72]):
        if i >= len(data['properties']['timeseries']):
            continue

        day_data = data['properties']['timeseries'][i]
        temp = day_data['data']['instant']['details']['air_temperature']

        if 'next_6_hours' in day_data['data']:
            symbol = day_data['data']['next_6_hours']['summary']['symbol_code']
        elif 'next_12_hours' in day_data['data']:
            symbol = day_data['data']['next_12_hours']['summary']['symbol_code']
        elif 'next_1_hours' in day_data['data']:
            symbol = day_data['data']['next_1_hours']['summary']['symbol_code']
        else:
            symbol = 'clearsky_day'

        time_string = day_data['time']
        date_obj = datetime.fromisoformat(time_string.replace('Z', '+00:00'))
        day_name_english = date_obj.strftime("%A")
        day_name_norwegian = norwegian_days[day_name_english][:3]  # Short day name

        emoji_forecast = weather_emoji.get(symbol, '🌡️')

        with day_cols[idx]:
            st.markdown(f"**{day_name_norwegian}**")
            st.markdown(f"{emoji_forecast} {temp}°C")