import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime, date
import pytz

def show():
    st.title("🏠 Hjem")
    

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("☀️ Været i dag")
        show_todays_weather()
    
    with col2:
        st.subheader("📅 I dag")
        show_todays_calendar()
    
    with col3:
        st.subheader("🍽️ Middag")
        show_todays_meal()

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
        
        emoji = weather_emoji.get(weather_symbol, '🌡️')
        symbol_base = weather_symbol.replace('_day', '').replace('_night', '')
        norwegian_name = weather_norwegian.get(symbol_base, weather_symbol)
        

        st.markdown(f"## {emoji} {temp_now}°C")
        st.write(f"**{norwegian_name}**")
        

        today_temps = []
        today = date.today()
        for i in range(24):
            if current_index + i < len(data['properties']['timeseries']):
                ts = data['properties']['timeseries'][current_index + i]
                dt = datetime.fromisoformat(ts['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
                if dt.date() == today:
                    today_temps.append(ts['data']['instant']['details']['air_temperature'])
        
        if today_temps:
            st.write(f"🔵 {min(today_temps)}°C | 🔴 {max(today_temps)}°C")
        
    except Exception as e:
        st.error("Kunne ikke laste vær")

def show_todays_calendar():

    
    try:
        from pages.calendar import get_calendar_events
        
        all_events = get_calendar_events()
        
        if not all_events:
            st.warning("Kunne ikke laste")
            return
        

        today = date.today()
        todays_events = []
        
        for e in all_events:
            if e['is_allday']:
                event_date = e['start']
            else:
                event_date = e['start'].date()
            
            if event_date == today:
                todays_events.append(e)
        
        if todays_events:
            for event in todays_events:
                if event['is_allday']:
                    if event.get('is_birthday'):
                        st.success(f"🎂 **{event['title']}**")
                    else:
                        st.write(f"📅 **{event['title']}**")
                else:
                    time_str = event['start'].strftime("%H:%M")
                    if event.get('is_birthday'):
                        st.success(f"🎉 **{time_str}**\n{event['title']}")
                    else:
                        st.write(f"🕐 **{time_str}**\n{event['title']}")
        else:
            st.info("Ingen hendelser")
            
    except Exception as e:
        st.error(f"Feil: {e}")

def show_todays_meal():
    """Viser dagens middag fra Google Sheets"""
    try:
        from pages.meals import get_meals
        
        meals = get_meals()
        
        if not meals:
            st.info("Ingen meny")
            return
        

        from datetime import datetime
        today = datetime.now().strftime("%A")
        norwegian_days = {
            'Monday': 'Mandag',
            'Tuesday': 'Tirsdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag',
            'Saturday': 'Lørdag',
            'Sunday': 'Søndag'
        }
        today_norwegian = norwegian_days.get(today, '')
        
        todays_meal = None
        for meal in meals:
            if meal.get('Dag') == today_norwegian:
                todays_meal = meal.get('Middag', 'Ikke planlagt')
                break
        
        if todays_meal:
            st.markdown(f"## {todays_meal}")
        else:
            st.info("Ikke planlagt")
            
    except Exception as e:
        st.info("Middag ikke tilgjengelig")