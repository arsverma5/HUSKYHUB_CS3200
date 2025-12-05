import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("👥 User Management")

# API URL
API_URL = "http://web-api:4000"

# Initialize session state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "View All Users"
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

# Check if coming from Reports page
if "search_user_id" in st.session_state and st.session_state.search_user_id:
    user_id = st.session_state.search_user_id
    st.session_state.search_user_id = None  # Clear it
    st.session_state.active_tab = "Search Users"
    
    # Fetch user details
    try:
        response = requests.get(f"{API_URL}/students/students/{user_id}")
        if response.status_code == 200:
            st.session_state.selected_user = response.json()
    except:
        st.error("Could not fetch user details") 
    
    st.rerun()  # Re-render page with new tab order

# Tabs - order changes based on active_tab
if st.session_state.active_tab == "Search Users":
    tab2, tab1, tab3 = st.tabs(["Search Users", "View All Users", "Suspensions"])
else:
    tab1, tab2, tab3 = st.tabs(["View All Users", "Search Users", "Suspensions"])    

# Show selected user at top if exists
if st.session_state.selected_user is not None:
    user = st.session_state.selected_user
    
    st.subheader(f"👤 {user.get('firstName')} {user.get('lastName')}")
    
    if st.button("✖ Close", key="close_user"):
        st.session_state.selected_user = None
        st.session_state.active_tab = "View All Users"
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**ID:** {user.get('stuId')}")
        st.write(f"**Email:** {user.get('email')}")
    with col2:
        st.write(f"**Status:** {user.get('accountStatus')}")
        st.write(f"**Verified:** {'✅' if user.get('verifiedStatus') else '❌'}")
    
    st.divider()

# View All Users tab
with tab1:
    st.subheader("View All Users")
    # ... rest of code

# Search Users tab
with tab2:
    st.subheader("Search Users")
    # ... rest of code

# Suspensions tab
with tab3:
    st.subheader("Suspensions")
    # ... rest of code