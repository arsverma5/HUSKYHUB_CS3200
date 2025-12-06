import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("👥 User Analytics")

# API URL
API_URL = "http://web-api:4000"