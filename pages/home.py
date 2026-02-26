import streamlit as st
from dotenv import load_dotenv
import os
from datetime import datetime, date
import pytz
from lists.english_norwegian import norwegian_days

def show():
    # Compact layout for 7" touchscreen (800x480)

    # Top row: Weather, Meal, Transport
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**☀️ Vær**")
        show_todays_weather()

    with col2:
        st.markdown("**🍽️ Middag**")
        show_todays_meal()

    with col3:
        st.markdown("**🚇 Avganger**")
        show_next_transport()

    # Bottom row: Calendar and News
    col4, col5 = st.columns(2)

    with col4:
        st.markdown("**📅 I dag**")
        show_todays_calendar()

    with col5:
        st.markdown("**📰 Nyheter**")
        show_top_news()

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
        

        st.markdown(f"### {emoji} {temp_now}°C - {norwegian_name}")

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
            for event in todays_events[:4]:  # Max 4 events on small screen
                title = event['title'][:30] + "..." if len(event['title']) > 30 else event['title']
                if event['is_allday']:
                    icon = "🎂" if event.get('is_birthday') else "📅"
                    st.caption(f"{icon} {title}")
                else:
                    time_str = event['start'].strftime("%H:%M")
                    icon = "🎉" if event.get('is_birthday') else "🕐"
                    st.caption(f"{icon} {time_str} {title}")
        else:
            st.caption("Ingen hendelser")
            
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
        

        today = datetime.now().strftime("%A")
        today_norwegian = norwegian_days.get(today, '')
        
        todays_meal = None
        for meal in meals:
            if meal.get('Dag') == today_norwegian:
                todays_meal = meal.get('Middag', 'Ikke planlagt')
                break
        
        if todays_meal:
            st.markdown(f"### {todays_meal}")
        else:
            st.caption("Ikke planlagt")
            
    except Exception as e:
        st.info("Middag ikke tilgjengelig")

def show_top_news():
    """Viser topp nyheter med sammendrag - compact for 7" screen"""
    try:
        from pages.news import get_top_headlines

        headlines = get_top_headlines(1)  # 1 from each source for home

        if headlines:
            for article in headlines:
                title = article['title'][:50] + "..." if len(article['title']) > 50 else article['title']
                st.caption(f"{article['source']} **{title}**")
                if article.get('summary'):
                    summary = article['summary'][:80] + "..." if len(article['summary']) > 80 else article['summary']
                    st.caption(f"_{summary}_")
        else:
            st.caption("Ingen nyheter")

    except Exception:
        st.caption("Nyheter utilgjengelig")

def show_next_transport():
    """Viser neste avganger - compact for 7" screen"""
    try:
        from pages.transport import get_next_departures, get_transport_icon, format_time_until

        departures = get_next_departures(4)

        if departures:
            for dep in departures:
                icon = get_transport_icon(dep['mode'])
                time_str = format_time_until(dep['time'])
                dest = dep['destination'][:12] + ".." if len(dep['destination']) > 12 else dep['destination']
                st.caption(f"{icon} {dep['line']} {dest} `{time_str}`")
        else:
            st.caption("Ingen avganger")

    except Exception:
        st.caption("Transport utilgjengelig")