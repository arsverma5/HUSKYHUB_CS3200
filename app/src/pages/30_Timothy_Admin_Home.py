# Page for admin to navigate to duties
# --------------------------------------------
# CONTENT:
# Button to Report Management
# Button to User Management
# Button to Listing Management
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
st.write('## Welcome to your dashboard, Timothy Green!')
st.write('#### What would you like to do today?')
st.divider()


# See Reports Management button
if st.button('Report Management', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/31_Reports_Management.py')

# See User Management page button
if st.button('User Management', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/32_User_Management.py')

# See Listing Management page button
if st.button('Listing Management', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/33_Listing_Management.py')