import streamlit as st
from dotenv import load_dotenv
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def show():
    load_dotenv()
    
    st.title("🍽️ Ukesmeny")
    
    try:
        # Google Sheets setup
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # Åpne sheet
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        sheet = client.open_by_key(sheet_id).sheet1
        
        # Hent data
        meals = sheet.get_all_records()
        
        # Vis ukesmeny
        for meal in meals:
            dag = meal['Dag']
            middag = meal['Middag']
            
            # Highlight dagens dag
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
                
    except Exception as e:
        st.error(f"Kunne ikke laste ukesmeny: {e}")
        st.write("Sjekk at Google Sheet er delt med service account!")