import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# Page config for 7-inch touchscreen (800x480)
st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Raspberry Pi 7" touchscreen
st.markdown("""
<style>
    /* Hide Streamlit branding and menu for kiosk mode */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}

    /* Reduce top padding */
    .block-container {
        padding-top: 0.25rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Compact touch-friendly buttons */
    .stButton > button {
        width: 100%;
        height: 38px;
        font-size: 14px;
        font-weight: bold;
        border-radius: 10px;
    }

    /* Collapse gap around nav button row */
    [data-testid="stHorizontalBlock"] {
        gap: 0.25rem;
        margin-bottom: 0;
    }

    /* Smaller headings to save space */
    h1 {
        font-size: 1.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.2rem !important;
    }
    h3 {
        font-size: 1rem !important;
    }

    /* Compact metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }

    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.25rem;
    }

    /* Smaller dividers */
    hr {
        margin: 0.5rem 0;
    }

    /* Compact expanders */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
    }

    /* Touch-friendly tabs */
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

st_autorefresh(interval=60000, key="page_refresh")


if 'page' not in st.session_state:
    st.session_state.page = 'home'
    
if 'last_interaction' not in st.session_state:
    st.session_state.last_interaction = time.time()


if st.session_state.page != 'home':
    if time.time() - st.session_state.last_interaction > 60:
        st.session_state.page = 'home'


col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button("🏠"):
        st.session_state.page = 'home'
        st.session_state.last_interaction = time.time()
with col2:
    if st.button("🌤️"):
        st.session_state.page = 'weather'
        st.session_state.last_interaction = time.time()
with col3:
    if st.button("📅"):
        st.session_state.page = 'calendar'
        st.session_state.last_interaction = time.time()
with col4:
    if st.button("🍽️"):
        st.session_state.page = 'meals'
        st.session_state.last_interaction = time.time()
with col5:
    if st.button("📰"):
        st.session_state.page = 'news'
        st.session_state.last_interaction = time.time()
with col6:
    if st.button("🚇"):
        st.session_state.page = 'transport'
        st.session_state.last_interaction = time.time()

st.markdown("<hr style='margin:2px 0'>", unsafe_allow_html=True)


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

elif st.session_state.page == 'news':
    import pages.news as news
    news.show()

elif st.session_state.page == 'transport':
    import pages.transport as transport
    transport.show()