import streamlit as st
import requests

@st.cache_data(ttl=600)  
def get_weather():
    """Henter værdata - cached i 10 minutter"""
    response = requests.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=59.91&lon=10.75",
        headers={"User-Agent": "MyWeatherDashboard/1.0"}
    )
    return response.json()