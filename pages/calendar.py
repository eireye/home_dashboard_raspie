import streamlit as st
from dotenv import load_dotenv
import os
import caldav
from datetime import datetime, timedelta, date
import pytz

def show():
    load_dotenv()
    
    st.title("📅 Kalender")
    
    try:
        url = "https://caldav.icloud.com"
        username = os.getenv('ICLOUD_EMAIL')
        password = os.getenv('ICLOUD_PASSWORD')
        
        client = caldav.DAVClient(url=url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        oslo_tz = pytz.timezone('Europe/Oslo')
        now = datetime.now(oslo_tz)
        start = now.replace(hour=0, minute=0, second=0)  # Start av i dag
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
                        
                        all_events.append({
                            'title': summary,
                            'start': dtstart,
                            'calendar': calendar.name
                        })
                    except:
                        continue
                        
            except:
                continue

        all_events.sort(key=lambda x: x['start'])
        

        today = date.today()
        todays_events = [e for e in all_events if (isinstance(e['start'], datetime) and e['start'].date() == today) or (isinstance(e['start'], date) and e['start'] == today)]
        upcoming_events = [e for e in all_events if e not in todays_events]
        
        
        st.subheader("I dag")
        if todays_events:
            for event in todays_events:
                dt = event['start']
                if isinstance(dt, datetime):
                    time_str = dt.strftime("%H:%M")
                    st.write(f"🕐 **{time_str}** - {event['title']}")
                else:
                    st.write(f"📅 {event['title']}")
        else:
            st.info("Ingen hendelser i dag")
      
        st.divider()
        st.subheader("Neste 7 dager")
        
        if upcoming_events:
            current_date = None
            for event in upcoming_events:
                dt = event['start']
                
                # Hent dato
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
                    st.write(f"  🕐 **{time_str}** - {event['title']}")
                else:
                    st.write(f"  📅 {event['title']}")
        else:
            st.info("Ingen kommende hendelser")
            
    except Exception as e:
        st.error(f"Kunne ikke laste kalender: {e}")