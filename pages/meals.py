import streamlit as st
from dotenv import load_dotenv
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

@st.cache_data(ttl=600)  # Cache i 10 minutter
def get_meals():
    """Henter ukesmeny fra Google Sheets - cached"""
    try:
        load_dotenv()
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        sheet = client.open_by_key(sheet_id).sheet1
        
        meals = sheet.get_all_records()
        return meals
    except Exception as e:
        return []

def show():
    st.title("Ukesmeny")
    
    meals = get_meals()
    
    if not meals:
        st.error("Kunne ikke laste ukesmeny")
        st.write("Sjekk at Google Sheet er delt med service account!")
        return
    

    for meal in meals:
        dag = meal.get('Dag', '')
        middag = meal.get('Middag', '')
        

        from datetime import datetime
        today = datetime.now().strftime("%A")
        norwegian_days = {
            'Monday': 'Mandag',
            'Tuesday': 'Tirsdag',
            'Wednesday': 'Onsdag',
            'Thursday': 'Torsdag',
            'Friday': 'Fredag',
            'Saturday': 'Lørdag',
            'Sunday': 'Søndag'
        }
        today_norwegian = norwegian_days.get(today, '')
        
        if dag == today_norwegian:
            st.success(f"**{dag}**: {middag} 🍴")
        else:
            st.write(f"**{dag}**: {middag}")