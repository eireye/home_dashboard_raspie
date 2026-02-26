import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configurable location - defaults to Oslo
WEATHER_LAT = os.getenv('WEATHER_LAT', '59.91')
WEATHER_LON = os.getenv('WEATHER_LON', '10.75')

@st.cache_data(ttl=600)
def get_weather():
    """Henter værdata fra yr.no/met.no - cached i 10 minutter"""
    response = requests.get(
        f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={WEATHER_LAT}&lon={WEATHER_LON}",
        headers={"User-Agent": "HomeDashboard/1.0"}
    )
    return response.json()