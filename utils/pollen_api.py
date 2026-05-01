import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

LAT = os.getenv('WEATHER_LAT', '59.91')
LON = os.getenv('WEATHER_LON', '10.75')

POLLEN_TYPES = {
    'alder_pollen':   {'label': 'Or',       'category': 'tree'},
    'birch_pollen':   {'label': 'Bjørk',    'category': 'tree'},
    'grass_pollen':   {'label': 'Gress',    'category': 'grass'},
    'mugwort_pollen': {'label': 'Burot',    'category': 'weed'},
    'ragweed_pollen': {'label': 'Ambrosia', 'category': 'weed'},
}

THRESHOLDS = {
    'tree':  [(10, 'lite', '🟢'), (100, 'moderat', '🟡'), (1000, 'kraftig', '🟠'), (float('inf'), 'ekstrem', '🔴')],
    'grass': [(5,  'lite', '🟢'), (20,  'moderat', '🟡'), (50,   'kraftig', '🟠'), (float('inf'), 'ekstrem', '🔴')],
    'weed':  [(5,  'lite', '🟢'), (20,  'moderat', '🟡'), (50,   'kraftig', '🟠'), (float('inf'), 'ekstrem', '🔴')],
}

COLOR_MAP = {
    'lite':    '#4caf50',
    'moderat': '#ff9800',
    'kraftig': '#ff5722',
    'ekstrem': '#f44336',
}

ADVICE = {
    'moderat': ['Vurder antihistamin ved utendørsaktivitet.'],
    'kraftig': [
        'Dusj og skift klær etter å ha vært ute.',
        'Lukk vinduer på dagtid.',
        'Husk medisin.',
    ],
    'ekstrem': [
        'Dusj og vask håret før leggetid.',
        'Hold vinduer lukket hele dagen.',
        'Begrens utendørsopphold midt på dagen.',
        'Ha medisin tilgjengelig.',
    ],
}


@st.cache_data(ttl=1800)
def get_pollen_data():
    params = {
        'latitude': LAT,
        'longitude': LON,
        'hourly': ','.join(POLLEN_TYPES.keys()),
        'timezone': 'Europe/Oslo',
        'forecast_days': 4,
    }
    r = requests.get(
        'https://air-quality-api.open-meteo.com/v1/air-quality',
        params=params,
        timeout=10,
    )
    r.raise_for_status()
    return r.json()


def classify(value, category):
    for threshold, level, emoji in THRESHOLDS[category]:
        if value <= threshold:
            return level, emoji
    return 'ekstrem', '🔴'


def get_advice(worst_level):
    return ADVICE.get(worst_level, [])
