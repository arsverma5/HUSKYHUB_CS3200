# Page for admin to view and manage listings
# --------------------------------------------
# CONTENT:
# See service history for a specific user (User story 3.4)
# See all listings (User story 3.3)
# -------------------------------------------

import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("🛠️ Listing Management")

# API URL
API_URL = "http://web-api:4000"

# Tabs
tab1, tab2 = st.tabs(["View All Listings", "Search For Listing"])

# All Listing Tab
with tab1:
    st.subheader("View All Listings")




