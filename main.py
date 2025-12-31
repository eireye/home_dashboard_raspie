import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time


st_autorefresh(interval=60000, key="page_refresh")


if 'page' not in st.session_state:
    st.session_state.page = 'home'
    
if 'last_interaction' not in st.session_state:
    st.session_state.last_interaction = time.time()


if st.session_state.page != 'home':
    if time.time() - st.session_state.last_interaction > 60:
        st.session_state.page = 'home'


col1, col2, col3, col4 = st.columns(4)  
with col1:
    if st.button("🏠 Hjem"):
        st.session_state.page = 'home'
        st.session_state.last_interaction = time.time()
with col2:
    if st.button("🌤️ Vær"):
        st.session_state.page = 'weather'
        st.session_state.last_interaction = time.time()
with col3:
    if st.button("📅 Kalender"):
        st.session_state.page = 'calendar'
        st.session_state.last_interaction = time.time()
with col4:
    if st.button("🍽️ Middag"):
        st.session_state.page = 'meals'
        st.session_state.last_interaction = time.time()

st.divider()


if st.session_state.page == 'home':
    import pages.home as home
    home.show()
    
elif st.session_state.page == 'weather':
    import pages.weather as weather
    weather.show()
    
elif st.session_state.page == 'calendar':
    import pages.calendar as calendar
    calendar.show()
    
elif st.session_state.page == 'meals':
    import pages.meals as meals
    meals.show()