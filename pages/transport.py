import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime
import pytz
import os
from dotenv import load_dotenv

load_dotenv()

# Entur API - free, no key required (covers all Norway including Ruter)
ENTUR_API = "https://api.entur.io/journey-planner/v3/graphql"

# Default stops - can be configured via environment variables
# Find stop IDs at https://stoppested.entur.org/
DEFAULT_STOPS = [
    {"id": "NSR:StopPlace:61268", "name": "Sinsen T"},
]

def get_configured_stops():
    """Get stops from environment or use defaults
    Format: NSR:StopPlace:12345=Name,NSR:StopPlace:67890=Name2
    """
    stops_env = os.getenv('TRANSPORT_STOPS', '')
    if stops_env:
        stops = []
        for stop in stops_env.split(','):
            # Split by = to separate ID from name
            if '=' in stop:
                stop_id, stop_name = stop.strip().split('=', 1)
                stops.append({"id": stop_id.strip(), "name": stop_name.strip()})
        if stops:
            return stops
    return DEFAULT_STOPS

@st.cache_data(ttl=60)
def get_departures(stop_id, num_departures=10):
    """Henter sanntids avganger fra Entur API"""
    query = """
    query($stopId: String!, $numDepartures: Int!) {
        stopPlace(id: $stopId) {
            name
            estimatedCalls(numberOfDepartures: $numDepartures) {
                expectedDepartureTime
                destinationDisplay {
                    frontText
                }
                serviceJourney {
                    line {
                        publicCode
                        transportMode
                    }
                }
            }
        }
    }
    """

    try:
        response = requests.post(
            ENTUR_API,
            json={"query": query, "variables": {"stopId": stop_id, "numDepartures": num_departures}},
            headers={
                "ET-Client-Name": "home-dashboard",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        data = response.json()

        if 'data' in data and data['data'] and data['data']['stopPlace']:
            stop = data['data']['stopPlace']
            departures = []
            for call in stop.get('estimatedCalls', []):
                dep_time = datetime.fromisoformat(call['expectedDepartureTime'].replace('Z', '+00:00'))
                oslo_tz = pytz.timezone('Europe/Oslo')
                dep_time_oslo = dep_time.astimezone(oslo_tz)

                departures.append({
                    'time': dep_time_oslo,
                    'line': call['serviceJourney']['line']['publicCode'],
                    'destination': call['destinationDisplay']['frontText'] or '',
                    'mode': call['serviceJourney']['line']['transportMode']
                })
            return {"name": stop['name'], "departures": departures}
        return None
    except Exception:
        return None

def get_transport_icon(mode):
    """Return emoji for transport mode"""
    icons = {
        'metro': '🚇',
        'bus': '🚌',
        'tram': '🚊',
        'rail': '🚆',
        'water': '⛴️',
        'air': '✈️',
    }
    return icons.get(mode.lower(), '🚏')

def format_time_until(dep_time):
    """Format time until departure"""
    now = datetime.now(pytz.timezone('Europe/Oslo'))
    diff = dep_time - now
    minutes = int(diff.total_seconds() / 60)

    if minutes < 1:
        return "Nå"
    elif minutes < 60:
        return f"{minutes} min"
    else:
        return dep_time.strftime("%H:%M")

def show():
    st_autorefresh(interval=60000, key="transport_refresh")

    stops = get_configured_stops()

    if len(stops) == 1:
        # Single stop - show directly
        stop = stops[0]
        data = get_departures(stop['id'])

        if data:
            st.markdown(f"**{data['name']}**")
            show_departures(data['departures'][:8])
        else:
            st.warning(f"Kunne ikke laste avganger for {stop['name']}")
    else:
        # Multiple stops - use tabs
        tab_names = [s['name'][:10] for s in stops]
        tabs = st.tabs(tab_names)

        for i, stop in enumerate(stops):
            with tabs[i]:
                data = get_departures(stop['id'])

                if data:
                    show_departures(data['departures'][:8])
                else:
                    st.warning("Kunne ikke laste avganger")

def show_departures(departures):
    """Display departures in compact format"""
    for dep in departures:
        icon = get_transport_icon(dep['mode'])
        time_str = format_time_until(dep['time'])
        line = dep['line']
        dest = dep['destination'][:20] + "..." if len(dep['destination']) > 20 else dep['destination']

        st.markdown(f"{icon} **{line}** {dest} — `{time_str}`")

def get_next_departures(count=3):
    """Get next departures for home page display"""
    stops = get_configured_stops()
    if not stops:
        return []

    all_departures = []
    for stop in stops[:2]:  # Max 2 stops for home page
        data = get_departures(stop['id'], 5)
        if data:
            for dep in data['departures'][:3]:
                all_departures.append({
                    'stop': stop['name'],
                    'line': dep['line'],
                    'destination': dep['destination'],
                    'time': dep['time'],
                    'mode': dep['mode']
                })

    # Sort by departure time
    all_departures.sort(key=lambda x: x['time'])
    return all_departures[:count]
