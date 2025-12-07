##################################################
# This is the main/entry-point file for the 
# sample application for your project
##################################################

# Set up basic logging infrastructure
import logging
logging.basicConfig(format='%(filename)s:%(lineno)s:%(levelname)s -- %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# import the main streamlit library as well
# as SideBarLinks function from src/modules folder
import streamlit as st
from modules.nav import SideBarLinks

# streamlit supports reguarl and wide layout (how the controls
# are organized/displayed on the screen).
st.set_page_config(layout = 'wide')

# If a user is at this page, we assume they are not 
# authenticated.  So we change the 'authenticated' value
# in the streamlit session_state to false. 
st.session_state['authenticated'] = False

# Use the SideBarLinks function from src/modules/nav.py to control
# the links displayed on the left-side panel. 
# IMPORTANT: ensure src/.streamlit/config.toml sets
# showSidebarNavigation = false in the [client] section
SideBarLinks(show_home=True)

# ***************************************************
#    The major content of this page
# ***************************************************

logger.info("Loading HuskyHub Home page")
st.title('🐾 HuskyHub - Campus Service Marketplace')
st.write('\n\n')
st.write('### Welcome to HuskyHub!')
st.write('Your trusted peer-to-peer service platform for Northeastern students.')
st.write('\n')
st.write('#### Select a user persona to explore:')

# For each of the user personas for which we are implementing
# functionality, we put a button on the screen that the user 
# can click to MIMIC logging in as that mock user. 

# Emma Chen - Student Client
if st.button("🎓 Act as Emma Chen - Student Client", 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'student_client'
    st.session_state['first_name'] = 'Emma'
    st.session_state['user_id'] = 1  # Emma's stuId from sample data
    logger.info("Logging in as Emma Chen - Student Client")
    st.switch_page('pages/10_Emma_Client_Home.py')

# Jessica Martinez - Service Provider
if st.button('💼 Act as Jessica Martinez - Service Provider', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'service_provider'
    st.session_state['first_name'] = 'Jessica'
    st.session_state['user_id'] = 3  # Jessica's stuId from sample data
    st.switch_page('pages/20_Jessica_Provider_Home.py')

# Timothy Green - Platform Admin
if st.button('🛡️ Act as Timothy Green - Platform Admin', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'admin'
    st.session_state['first_name'] = 'Timothy'
    st.switch_page('pages/30_Timothy_Admin_Home.py')

# Chris Chan - Product Manager
if st.button('📊 Act as Chris Chan - Product Manager', 
            type='primary', 
            use_container_width=True):
    st.session_state['authenticated'] = True
    st.session_state['role'] = 'PM'
    st.session_state['first_name'] = 'Chris'
    st.switch_page('pages/40_Chris_PM_Home.py')