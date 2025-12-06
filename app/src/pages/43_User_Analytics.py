import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks


st.set_page_config(page_title="User Analytics", page_icon="👥", layout="wide")
SideBarLinks(show_home=True)

st.title("👥 User Analytics")
st.write("Analyze user behavior and trends")

# API URL
API_URL = "http://web-api:4000"