import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# Auto-refresh hver 60 sekunder (sjekker om vi skal tilbake til vær)
st_autorefresh(interval=60000, key="page_refresh")

# Initialiser session state
if 'page' not in st.session_state:
    st.session_state.page = 'weather'
    
if 'last_interaction' not in st.session_state:
    st.session_state.last_interaction = time.time()

# Sjekk om vi skal tilbake til vær
if st.session_state.page != 'weather':
    if time.time() - st.session_state.last_interaction > 60:
        st.session_state.page = 'weather'

# Navigation knapper
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🌤️ Vær"):
        st.session_state.page = 'weather'
        st.session_state.last_interaction = time.time()
with col2:
    if st.button("📅 Kalender"):
        st.session_state.page = 'calendar'
        st.session_state.last_interaction = time.time()
with col3:
    if st.button("🍽️ Middag"):
        st.session_state.page = 'meals'
        st.session_state.last_interaction = time.time()

st.divider()

# Vis riktig side
if st.session_state.page == 'weather':
    import pages.weather as weather
    weather.show()
    
elif st.session_state.page == 'calendar':
    import pages.calendar as calendar
    calendar.show()
    
elif st.session_state.page == 'meals':
    st.title("🍽️ Middagsplan")
    st.write("tentativt")