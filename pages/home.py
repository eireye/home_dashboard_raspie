import streamlit as st
from dotenv import load_dotenv
import os
import caldav
import requests
from datetime import datetime, timedelta, date
import pytz

def show():
    st.title("🏠 Hjem")
    
    # To kolonner: Vær til venstre, Kalender til høyre
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Været i dag")
        show_todays_weather()
    
    with col2:
        st.subheader("📅 I dag")
        show_todays_calendar()

def show_todays_weather():
    """Viser dagens vær - kompakt versjon"""
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
        
        # Vis temperatur og vær
        st.markdown(f"## {emoji} {temp_now}°C")
        st.write(f"**{norwegian_name}**")
        
        # Min/max i dag
        today_temps = []
        today = date.today()
        for i in range(24):
            if current_index + i < len(data['properties']['timeseries']):
                ts = data['properties']['timeseries'][current_index + i]
                dt = datetime.fromisoformat(ts['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
                if dt.date() == today:
                    today_temps.append(ts['data']['instant']['details']['air_temperature'])
        
        if today_temps:
            st.write(f"🔵 Min: {min(today_temps)}°C | 🔴 Max: {max(today_temps)}°C")
        
    except Exception as e:
        st.error(f"Kunne ikke laste vær: {e}")

def show_todays_calendar():
    """Viser dagens kalender - kompakt versjon"""
    load_dotenv()
    
    try:
        url = "https://caldav.icloud.com"
        username = os.getenv('ICLOUD_EMAIL')
        password = os.getenv('ICLOUD_PASSWORD')
        
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        oslo_tz = pytz.timezone('Europe/Oslo')
        now = datetime.now(oslo_tz)
        start = now.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=1)
        
        all_events = []
        
        for calendar in calendars:
            if "minner" in calendar.name.lower():
                continue
                
            try:
                events = calendar.date_search(start=start, end=end)
                
                for event in events:
                    try:
                        event.load()
                        if not hasattr(event, 'vobject_instance'):
                            continue
                        
                        vobj = event.vobject_instance
                        if not hasattr(vobj, 'vevent'):
                            continue
                            
                        vevent = vobj.vevent
                        summary = vevent.summary.value if hasattr(vevent, 'summary') else 'Uten tittel'
                        dtstart = vevent.dtstart.value if hasattr(vevent, 'dtstart') else None
                        
                        if dtstart is None:
                            continue
                        
                        is_birthday = 'bursdag' in summary.lower() or 'birthday' in summary.lower() or '🎂' in summary or '🎉' in summary
                        
                        all_events.append({
                            'title': summary,
                            'start': dtstart,
                            'is_birthday': is_birthday
                        })
                    except:
                        continue
            except:
                continue
        
        all_events.sort(key=lambda x: x['start'])
        
        if all_events:
            for event in all_events:
                dt = event['start']
                if isinstance(dt, datetime):
                    time_str = dt.strftime("%H:%M")
                    if event['is_birthday']:
                        st.success(f"🎉 **{time_str}** - {event['title']}")
                    else:
                        st.write(f"🕐 **{time_str}** - {event['title']}")
                else:
                    if event['is_birthday']:
                        st.success(f"🎂 {event['title']}")
                    else:
                        st.write(f"📅 {event['title']}")
        else:
            st.info("Ingen hendelser i dag")
            
    except Exception as e:
        st.error("Kunne ikke laste kalender")