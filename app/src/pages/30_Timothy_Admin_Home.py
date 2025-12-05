import streamlit as st
from modules.nav import SideBarLinks 
import requests


# Show sidebar navigation
SideBarLinks(show_home=True)


# Set page layout
st.set_page_config(layout = 'wide')

# Title the page
st.title('🐾 HuskyHub')
st.divider()
st.write('#### Welcome to your dashboard, Timothy Green!')

# See reports button
if st.button('See All Reports', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/31_Reports_Management.py')

# See User Management page button
if st.button('See User Management', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/32_User_Management.py')