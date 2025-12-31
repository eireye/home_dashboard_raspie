import streamlit as st
from dotenv import load_dotenv
import os
import caldav
from datetime import datetime, timedelta, date
import pytz

@st.cache_data(ttl=300)
def get_calendar_events():

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
                        

                        is_allday = isinstance(dtstart, date) and not isinstance(dtstart, datetime)
                        

                        if is_allday:
                            dtstart_sort = datetime.combine(dtstart, datetime.min.time())
                            dtstart_sort = oslo_tz.localize(dtstart_sort)
                        else:
                            dtstart_sort = dtstart
                        
                        all_events.append({
                            'title': summary,
                            'start': dtstart,  
                            'start_sort': dtstart_sort, 
                            'calendar': calendar.name,
                            'is_birthday': is_birthday,
                            'is_allday': is_allday
                        })
                    except Exception as e:
                        # Skip events som feiler
                        continue
                        
            except:
                continue
        
        # Sorter etter start_sort
        all_events.sort(key=lambda x: x['start_sort'])
        return all_events
        
    except Exception as e:
        return []

def show():
    st.title("📅 Kalender")
    
    all_events = get_calendar_events()
    
    if not all_events:
        st.warning("Kunne ikke laste kalender. Prøver igjen om 5 minutter...")
        return
    
    # Del opp i dagens og fremtidige
    today = date.today()
    todays_events = []
    upcoming_events = []
    
    for e in all_events:
        if e['is_allday']:
            event_date = e['start']  # Allerede date
        else:
            event_date = e['start'].date()
        
        if event_date == today:
            todays_events.append(e)
        elif event_date > today:
            upcoming_events.append(e)
    
    # Vis bursdager først
    birthdays = [e for e in all_events if e['is_birthday']]
    if birthdays:
        st.markdown("### 🎉 Kommende bursdager!")
        for event in birthdays[:3]:
            if event['is_allday']:
                date_str = event['start'].strftime("%d.%m")
            else:
                date_str = event['start'].strftime("%d.%m")
            
            st.success(f"🎂 **{event['title']}** - {date_str}")
        st.divider()
    

    st.subheader("I dag")
    if todays_events:
        for event in todays_events:
            if event['is_allday']:
                if event['is_birthday']:
                    st.success(f"🎂 **{event['title']}**")
                else:
                    st.write(f"📅 **{event['title']}**")
            else:
                # Event med tid
                time_str = event['start'].strftime("%H:%M")
                if event['is_birthday']:
                    st.success(f"🎉 **{time_str}** - {event['title']}")
                else:
                    st.write(f"🕐 **{time_str}** - {event['title']}")
    else:
        st.info("Ingen hendelser i dag")
    

    st.divider()
    st.subheader("Neste 7 dager")
    
    if upcoming_events:
        current_date = None
        for event in upcoming_events:
            if event['is_allday']:
                event_date = event['start']
            else:
                event_date = event['start'].date()
            
            if event_date != current_date:
                current_date = event_date
                day_name = event_date.strftime("%A")
                date_str = event_date.strftime("%d.%m")
                st.write(f"### {day_name} {date_str}")
            
            if event['is_allday']:

                if event['is_birthday']:
                    st.success(f"  🎂 **{event['title']}**")
                else:
                    st.write(f"  📅 **{event['title']}**")
            else:
                time_str = event['start'].strftime("%H:%M")
                if event['is_birthday']:
                    st.success(f"  🎉 **{time_str}** - {event['title']}")
                else:
                    st.write(f"  🕐 **{time_str}** - {event['title']}")
    else:
        st.info("Ingen kommende hendelser")