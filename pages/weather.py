import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, date
import pytz
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
    emoji = weather_emoji.get(weather_symbol, '')
    symbol_base = weather_symbol.replace('_day', '').replace('_night', '')
    norwegian_name = weather_norwegian.get(symbol_base, weather_symbol)

    st.markdown(f"## {emoji} {temp_now}°C — {norwegian_name}")

    # Min/max today
    today_temps = []
    today = date.today()
    for i in range(24):
        if current_index + i < len(data['properties']['timeseries']):
            ts = data['properties']['timeseries'][current_index + i]
            dt = datetime.fromisoformat(ts['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
            if dt.date() == today:
                today_temps.append(ts['data']['instant']['details']['air_temperature'])
    if today_temps:
        st.caption(f"↓ {min(today_temps)}°C  |  ↑ {max(today_temps)}°C")

    st.divider()

    # Next 12 hours as simple text
    st.markdown("**Neste 12 timer**")
    cols = st.columns(6)
    for idx, i in enumerate(range(current_index, min(current_index + 6, len(data['properties']['timeseries'])))):
        hour_data = data['properties']['timeseries'][i]
        time_obj = datetime.fromisoformat(hour_data['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
        temp = hour_data['data']['instant']['details']['air_temperature']
        symbol = hour_data['data'].get('next_1_hours', {}).get('summary', {}).get('symbol_code', '')
        em = weather_emoji.get(symbol, '')
        with cols[idx]:
            st.caption(time_obj.strftime("%H:%M"))
            st.markdown(f"**{temp}°**")
            st.caption(em)

    st.divider()

    # 3-day forecast
    st.markdown("**3 dager**")
    day_cols = st.columns(3)
    for idx, i in enumerate([24, 48, 72]):
        if i >= len(data['properties']['timeseries']):
            continue
        day_data = data['properties']['timeseries'][i]
        temp = day_data['data']['instant']['details']['air_temperature']
        symbol = (day_data['data'].get('next_6_hours') or day_data['data'].get('next_12_hours') or day_data['data'].get('next_1_hours', {})).get('summary', {}).get('symbol_code', '')
        date_obj = datetime.fromisoformat(day_data['time'].replace('Z', '+00:00'))
        day_name = norwegian_days.get(date_obj.strftime("%A"), '')[:3]
        em = weather_emoji.get(symbol, '')
        with day_cols[idx]:
            st.markdown(f"**{day_name}**")
            st.markdown(f"{em} {temp}°C")
