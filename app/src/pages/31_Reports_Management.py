import streamlit as st
from modules.nav import SideBarLinks 
import requests

st.set_page_config(page_title="Admin Reports", layout="wide")
st.title("Reports History")
st.session_state['role'] = 'admin'

# Show SideBarLinks
SideBarLinks(show_home=True)
