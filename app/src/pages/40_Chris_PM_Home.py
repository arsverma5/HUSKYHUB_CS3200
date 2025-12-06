# Page for PM to navigate to duties
# --------------------------------------------
# CONTENT:
# Button to Growth Dashboard
# Button to Category Analytics
# Button to User Analytics
# -------------------------------------------


import streamlit as st
from modules.nav import SideBarLinks 
import requests

# Show sidebar navigation
SideBarLinks(show_home=True)


# Set page layout
st.set_page_config(layout = 'wide')

# Title the page
st.title('🐾 HuskyHub')
st.write('## Welcome to your dashboard, Chris Chan!')
st.write('#### What would you like to do today?')
st.divider()

# See Growth Dashboard button
if st.button('Growth Dashboard', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'PM'
    st.session_state['first_name'] = 'Chris'
    st.switch_page('pages/41_Growth_Dashboard.py')

# See Category Analytics page button
if st.button('Category Analytics', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'PM'
    st.session_state['first_name'] = 'Chris'
    st.switch_page('pages/42_Category_Analytics.py')

# See User Analytics page button
if st.button('User Analytics', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'PM'
    st.session_state['first_name'] = 'Chris'
    st.switch_page('pages/43_User_Analytics.py')