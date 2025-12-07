import logging
logger = logging.getLogger(__name__)

import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title(f"Welcome Student, {st.session_state['first_name']}! 🎓")
st.write('')
st.write('')
st.write('### What would you like to do today?')

# Button to browse services (User Story 1.1)
if st.button('Browse & Search Services', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/11_Browse_Services.py')

# Button to view provider profiles (User Story 1.2)
if st.button('View Provider Profiles', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/12_Provider_Profile.py')

# Button to view my bookings (User Story 1.3)
if st.button('My Bookings & Appointments', 
             type='primary',
             use_container_width=True):
    st.switch_page('pages/13_My_Bookings.py')

# Quick stats for Emma
st.write('')
st.write('---')
st.write('### Quick Stats')

try:
    import requests
    # Get Emma's booking count
    response = requests.get(f'http://web-api:4000/transactions/?buyerId={st.session_state["user_id"]}')
    if response.status_code == 200:
        bookings = response.json()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Bookings", len(bookings))
        
        with col2:
            pending = len([b for b in bookings if b.get('transactStatus') == 'requested'])
            st.metric("Pending Requests", pending)
        
        with col3:
            completed = len([b for b in bookings if b.get('transactStatus') == 'completed'])
            st.metric("Completed Services", completed)
except Exception as e:
    st.info("Unable to load stats at this time")