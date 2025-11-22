import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
from datetime import datetime, timezone
import pytz
import pandas as pd
from lists.english_norwegian import weather_norwegian, norwegian_days
from lists.weather_emoji import weather_emoji



st_autorefresh(interval=600000, key="weather_refresh")

@st.cache_data(ttl=600)  
def get_weather():
    response = requests.get(
        "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=59.91&lon=10.75",
        headers={"User-Agent": "MyWeatherDashboard/1.0"}
    )
    return response.json()


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



st.title("🏠 XXX dashboard") # tentativ name
st.metric(label="Temperatur nå", value=f"{temp_now}°C")
st.write(f"### {emoji} {norwegian_name}")
st.subheader("Temperatur neste 24 timer")

hours = []
temps = []


for i in range(current_index, current_index + 24):
    hour_data = data['properties']['timeseries'][i]
    # Konverter til norsk tid
    time_obj = datetime.fromisoformat(hour_data['time'].replace('Z', '+00:00'))  # TRENGER DENNE!
    time_oslo = time_obj.astimezone(oslo_tz)  
    hour = time_oslo.strftime("%H:%M")
    temp = hour_data['data']['instant']['details']['air_temperature']
    
    hours.append(hour)
    temps.append(temp)
# Lag chart
chart_data = pd.DataFrame({
    'Tid': hours,
    'Temperatur': temps
})
chart_data = chart_data.set_index('Tid')


st.line_chart(chart_data)

# Vis min/max
min_temp = min(temps)
max_temp = max(temps)
st.write(f"🔵 Lavest: {min_temp}°C  |  🔴 Høyest: {max_temp}°C")

st.divider()

st.subheader("Neste 3 dager")

for i in [24, 48, 72]:
    day_data = data['properties']['timeseries'][i]
    temp = day_data['data']['instant']['details']['air_temperature']
    
    # Prøv å finne værdata - ta det som finnes
    if 'next_6_hours' in day_data['data']:
        symbol = day_data['data']['next_6_hours']['summary']['symbol_code']
    elif 'next_12_hours' in day_data['data']:
        symbol = day_data['data']['next_12_hours']['summary']['symbol_code']
    elif 'next_1_hours' in day_data['data']:
        symbol = day_data['data']['next_1_hours']['summary']['symbol_code']
    else:
        symbol = 'clearsky_day'  # Fallback
    
    # Konverter dato
    time_string = day_data['time']
    date_obj = datetime.fromisoformat(time_string.replace('Z', '+00:00'))
    day = date_obj.day
    month = date_obj.month
    day_name_english = date_obj.strftime("%A")
    day_name_norwegian = norwegian_days[day_name_english]
    formatted_date = f"{day_name_norwegian} {day}.{month:02d}"
    
    # Get emoji and Norwegian name
    emoji_forecast = weather_emoji.get(symbol, '🌡️')
    symbol_base_forecast = symbol.replace('_day', '').replace('_night', '')
    norwegian_forecast = weather_norwegian.get(symbol_base_forecast, symbol)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**{formatted_date}**")
    with col2:
        st.write(f"{emoji_forecast} {temp}°C - {norwegian_forecast}")