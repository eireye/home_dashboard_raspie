import streamlit as st
from datetime import datetime, date, timedelta
import pytz
from lists.english_norwegian import norwegian_days

def show():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Vær**")
        show_todays_weather()

    with col2:
        st.markdown("**I dag**")
        show_todays_calendar()

    with col3:
        st.markdown("**Middag**")
        show_todays_meal()
        st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)
        show_top_news()

def show_todays_weather():
    try:
        from utils.weather_api import get_weather
        from lists.weather_emoji import weather_emoji
        from lists.english_norwegian import weather_norwegian
        data = get_weather()
        oslo_tz = pytz.timezone('Europe/Oslo')
        now_oslo = datetime.now(oslo_tz)
        today = date.today()

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
        rain_warning = False
        cold_warning = False

        for i in range(1, 24):
            if current_index + i >= len(data['properties']['timeseries']):
                break
            ts = data['properties']['timeseries'][current_index + i]
            dt = datetime.fromisoformat(ts['time'].replace('Z', '+00:00')).astimezone(oslo_tz)
            if dt.date() != today:
                break

            temp = ts['data']['instant']['details']['air_temperature']
            today_temps.append(temp)

            if 'next_1_hours' in ts['data']:
                details = ts['data']['next_1_hours'].get('details', {})
                precip = details.get('precipitation_amount', 0)
                sym = ts['data']['next_1_hours'].get('summary', {}).get('symbol_code', '')
                sym_base = sym.replace('_day', '').replace('_night', '')
                # Significant rain: not just "light" prefix
                has_rain_symbol = (
                    ('rain' in sym_base or 'sleet' in sym_base) and
                    not sym_base.startswith('light')
                )
                if precip >= 1.5 or has_rain_symbol:
                    rain_warning = True

            # Cold warning: drops 5°C+ from now AND goes below 8°C
            if (temp_now - temp) >= 5 and temp <= 8:
                cold_warning = True

        if today_temps:
            st.caption(f"↓{min(today_temps)}° ↑{max(today_temps)}°")
        if rain_warning:
            st.caption("☂️ Husk paraply!")
        if cold_warning:
            st.caption("🧥 Husk varm jakke!")

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
        week_end = today + timedelta(days=7)

        # Upcoming birthdays within 7 days
        upcoming_birthdays = []
        for e in all_events:
            e_date = e['start'] if e['is_allday'] else e['start'].date()
            if e.get('is_birthday') and e_date >= today and e_date <= week_end:
                upcoming_birthdays.append(e)
        for bday in upcoming_birthdays[:2]:
            b_date = bday['start'] if bday['is_allday'] else bday['start'].date()
            title = bday['title'][:22] + ".." if len(bday['title']) > 22 else bday['title']
            if b_date == today:
                st.caption(f"🎂 **{title}**")
            else:
                st.caption(f"🎂 {b_date.strftime('%d.%m')} {title}")

        # Today's non-birthday events
        todays_events = [
            e for e in all_events
            if (e['start'] if e['is_allday'] else e['start'].date()) == today
            and not e.get('is_birthday')
        ]
        if todays_events:
            for event in todays_events[:3]:
                title = event['title'][:22] + ".." if len(event['title']) > 22 else event['title']
                if event['is_allday']:
                    st.caption(f"📅 {title}")
                else:
                    st.caption(f"🕐 {event['start'].strftime('%H:%M')} {title}")
        elif not upcoming_birthdays:
            st.caption("Ingen hendelser")

        # Up to 3 upcoming non-birthday events from the rest of the week
        upcoming = [
            e for e in all_events
            if (e['start'] if e['is_allday'] else e['start'].date()) > today
            and not e.get('is_birthday')
        ]
        for event in upcoming[:3]:
            e_date = event['start'] if event['is_allday'] else event['start'].date()
            title = event['title'][:20] + ".." if len(event['title']) > 20 else event['title']
            if event['is_allday']:
                st.caption(f"📅 {e_date.strftime('%d.%m')} {title}")
            else:
                st.caption(f"🕐 {e_date.strftime('%d.%m')} {event['start'].strftime('%H:%M')} {title}")
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

def show_top_news():
    try:
        from pages.news import get_top_headlines
        headlines = get_top_headlines(count=3)
        for h in headlines:
            title = h['title'][:45] + ".." if len(h['title']) > 45 else h['title']
            if h.get('link'):
                st.caption(f"{h['source']} [{title}]({h['link']})")
            else:
                st.caption(f"{h['source']} {title}")
    except:
        pass
