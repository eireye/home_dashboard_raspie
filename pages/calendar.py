import streamlit as st
from dotenv import load_dotenv
import os
import caldav
from datetime import datetime, timedelta, date
import pytz

@st.cache_data(ttl=300)  # Cache i 5 minutter
def get_calendar_events():
    """Henter kalender-events med caching"""
    try:
        load_dotenv()
        url = "https://caldav.icloud.com"
        username = os.getenv('ICLOUD_EMAIL')
        password = os.getenv('ICLOUD_PASSWORD')
        
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        oslo_tz = pytz.timezone('Europe/Oslo')
        now = datetime.now(oslo_tz)
        start = now.replace(hour=0, minute=0, second=0)
        end = start + timedelta(days=7)
        
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
                            'calendar': calendar.name,
                            'is_birthday': is_birthday
                        })
                    except:
                        continue
                        
            except:
                continue
        
        all_events.sort(key=lambda x: x['start'])
        return all_events
        
    except Exception as e:
        return []

def show():
    st.title("📅 Kalender")
    
    # Hent events (cached)
    all_events = get_calendar_events()
    
    if not all_events:
        st.warning("Kunne ikke laste kalender. Prøver igjen om 5 minutter...")
        return
    
    # Del opp i dagens og fremtidige
    today = date.today()
    todays_events = [e for e in all_events if (isinstance(e['start'], datetime) and e['start'].date() == today) or (isinstance(e['start'], date) and e['start'] == today)]
    upcoming_events = [e for e in all_events if e not in todays_events]
    
    # Vis bursdager først
    birthdays = [e for e in all_events if e['is_birthday']]
    if birthdays:
        st.markdown("### 🎉 Kommende bursdager!")
        for event in birthdays[:3]:
            dt = event['start']
            if isinstance(dt, datetime):
                date_str = dt.strftime("%d.%m")
            else:
                date_str = dt.strftime("%d.%m")
            
            st.success(f"🎂 **{event['title']}** - {date_str}")
        st.divider()
    
    # Vis dagens hendelser
    st.subheader("I dag")
    if todays_events:
        for event in todays_events:
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
    
    # Vis neste 7 dager
    st.divider()
    st.subheader("Neste 7 dager")
    
    if upcoming_events:
        current_date = None
        for event in upcoming_events:
            dt = event['start']
            
            if isinstance(dt, datetime):
                event_date = dt.date()
            else:
                event_date = dt
            
            if event_date != current_date:
                current_date = event_date
                day_name = event_date.strftime("%A")
                date_str = event_date.strftime("%d.%m")
                st.write(f"### {day_name} {date_str}")
            
            if isinstance(dt, datetime):
                time_str = dt.strftime("%H:%M")
                if event['is_birthday']:
                    st.success(f"  🎉 **{time_str}** - {event['title']}")
                else:
                    st.write(f"  🕐 **{time_str}** - {event['title']}")
            else:
                if event['is_birthday']:
                    st.success(f"  🎂 {event['title']}")
                else:
                    st.write(f"  📅 {event['title']}")
    else:
        st.info("Ingen kommende hendelser")