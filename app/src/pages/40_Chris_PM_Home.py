# Page for PM to navigate to duties
# --------------------------------------------
# CONTENT:
# Button to Growth Dashboard
# Button to Category Analytics
# Button to User Analytics
# -------------------------------------------


from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
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
    
# give at a glance stats
st.divider()
st.subheader("At a Glance Stats")


# get total users
try:
        response = requests.get("http://web-api:4000/students")
   
        if response.status_code == 200:
                data = response.json()
                total_users = len(data)
        
        else:
                total_users = "N/A"
                
except Exception as e:
        total_users = "N/A"
        st.error("Error fetching total users")

# get total listings
try:
        response = requests.get("http://web-api:4000/listings")
    
        if response.status_code == 200:
                data = response.json()

                total_listings = len(data)
                new_listings = len([listing for listing in data if parsedate_to_datetime(listing['lastUpdate']) >= datetime.now(timezone.utc) - timedelta(days=30)])
                old_listings = total_listings - new_listings
                percent_increase_listings = str(round((new_listings / old_listings) * 100)) + "%" if old_listings > 0 else "100%"
        else:
                total_listings = "N/A"
                percent_increase_listings = "N/A"
        
except Exception as e:
        total_listings = "N/A"
        percent_increase_listings = "N/A"
        st.error("Error fetching total listings")
        
# get total transactions
try:
        response = requests.get("http://web-api:4000/transactions")
    
        if response.status_code == 200:
                data = response.json()
                total_transactions = len(data)
                st.write(data[0]['fulfillmentDate'])
                new_transactions = len([txn for txn in data if txn['fulfillmentDate'] and (parsedate_to_datetime(txn['fulfillmentDate']) >= datetime.now(timezone.utc) - timedelta(days=30))])
                old_transactions = total_transactions - new_transactions
                percent_increase_transactions = str(round((new_transactions / old_transactions) * 100)) + "%" if old_transactions > 0 else "100%"
        else:
                total_transactions = "N/A"
                percent_increase_transactions = "N/A"

except Exception as e:
        total_transactions = "N/A"
        percent_increase_transactions = "N/A"
        st.error("Error fetching total transactions")

    
col1, col2, col3 = st.columns(3)
with col1:
        st.metric("Total Users", total_users)
with col2:
        st.metric("Total Listings", total_listings, percent_increase_listings)
with col3:
        st.metric("Total Transactions", total_transactions, percent_increase_transactions)