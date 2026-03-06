import streamlit as st
from datetime import datetime, date
import pytz
from lists.english_norwegian import norwegian_days

def show():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Vær**")
        show_todays_weather()

    with col2:
        st.markdown("**Middag**")
        show_todays_meal()

    with col3:
        st.markdown("**I dag**")
        show_todays_calendar()

def show_todays_weather():
    try:
        from utils.weather_api import get_weather
        from lists.weather_emoji import weather_emoji
        from lists.english_norwegian import weather_norwegian
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
        st.markdown(f"**{emoji} {temp_now}°C**")
        st.caption(norwegian_name)
        today_temps = []
        today = date.today()
        for i in range(24):
            if current_index + i < len(data['properties']['timeseries']):
                ts = data['properties']['timeseries'][current_index + i]
                dt = datetime.fromisoformat(ts['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
                if dt.date() == today:
                    today_temps.append(ts['data']['instant']['details']['air_temperature'])
        if today_temps:
            st.caption(f"↓{min(today_temps)}° ↑{max(today_temps)}°")
    except:
        st.caption("Ikke tilgjengelig")

def show_todays_calendar():
    try:
        from pages.calendar import get_calendar_events
        all_events = get_calendar_events()
        if not all_events:
            st.caption("Ingen hendelser")
            return
        today = date.today()
        todays_events = [e for e in all_events if (e['start'] if e['is_allday'] else e['start'].date()) == today]
        if todays_events:
            for event in todays_events[:4]:
                title = event['title'][:25] + ".." if len(event['title']) > 25 else event['title']
                if event['is_allday']:
                    st.caption(f"{'🎂' if event.get('is_birthday') else '📅'} {title}")
                else:
                    st.caption(f"🕐 {event['start'].strftime('%H:%M')} {title}")
        else:
            st.caption("Ingen hendelser")
    except:
        st.caption("Ikke tilgjengelig")

def show_todays_meal():
    try:
        from pages.meals import get_meals
        meals = get_meals()
        if not meals:
            st.caption("Ikke planlagt")
            return
        today_norwegian = norwegian_days.get(datetime.now().strftime("%A"), '')
        todays_meal = next((m.get('Middag') for m in meals if m.get('Dag') == today_norwegian), None)
        if todays_meal:
            st.markdown(f"**{todays_meal}**")
        else:
            st.caption("Ikke planlagt")
    except:
        st.caption("Ikke tilgjengelig")
