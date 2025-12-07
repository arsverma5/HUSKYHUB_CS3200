import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

st.set_page_config(page_title="My Availability", page_icon="📅", layout="wide")
SideBarLinks()

st.title("📅 My Availability")
st.write("Set when you're available to provide services")

# Set provider ID
provider_id = 3

st.divider()

# SELECT WHICH SERVICE TO SET AVAILABILITY FOR
st.subheader("1️⃣ Select Service")

try:
    # Get provider's listings
    listings_response = requests.get(f'http://web-api:4000/l/listings')
    
    if listings_response.status_code == 200:
        all_listings = listings_response.json()
        my_listings = [l for l in all_listings if l.get('providerId') == provider_id]
        
        if len(my_listings) == 0:
            st.warning("You don't have any services yet. Create one first!")
            if st.button("Go to My Services"):
                st.switch_page("pages/21_My_Services.py")
            st.stop()
        
        # Create dropdown of services
        listing_options = {f"{l['title']} (${l['price']}/{l['unit']})": l['listingId'] 
                          for l in my_listings if l['listingStatus'] == 'active'}
        
        selected_service = st.selectbox("Choose a service:", list(listing_options.keys()))
        selected_listing_id = listing_options[selected_service]
        
except Exception as e:
    st.error(f"Error loading services: {str(e)}")
    st.stop()

st.divider()

# ADD NEW AVAILABILITY
st.subheader("2️⃣ Add Availability")

col1, col2 = st.columns(2)

with col1:
    st.write("**Single Time Slot**")
    
    date = st.date_input("Date", min_value=datetime.now().date())
    start_time = st.time_input("Start Time", value=datetime.now().time())
    end_time = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time())
    
    if st.button("➕ Add Single Slot", use_container_width=True, type="primary"):
        try:
            start_datetime = f"{date} {start_time}"
            end_datetime = f"{date} {end_time}"
            
            response = requests.post(
                f'http://web-api:4000/l/listings/{selected_listing_id}/availability',
                json={
                    'slots': [
                        {
                            'startTime': start_datetime,
                            'endTime': end_datetime
                        }
                    ]
                }
            )
            
            if response.status_code == 201:
                st.success("✅ Availability added!")
                st.rerun()
            else:
                st.error(f"Failed to add availability: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

with col2:
    st.write("**Recurring Weekly Slots**")
    
    day_of_week = st.selectbox(
        "Day of Week",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )
    recurring_start = st.time_input("Start Time", value=datetime.now().time(), key="recurring_start")
    recurring_end = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time(), key="recurring_end")
    num_weeks = st.number_input("Number of Weeks", min_value=1, max_value=12, value=4)
    
    if st.button("➕ Add Recurring Slots", use_container_width=True):
        try:
            # Generate dates for the next N weeks on selected day
            slots = []
            day_map = {
                "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                "Friday": 4, "Saturday": 5, "Sunday": 6
            }
            
            today = datetime.now().date()
            days_ahead = day_map[day_of_week] - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            
            next_occurrence = today + timedelta(days=days_ahead)
            
            for week in range(num_weeks):
                slot_date = next_occurrence + timedelta(weeks=week)
                slots.append({
                    'startTime': f"{slot_date} {recurring_start}",
                    'endTime': f"{slot_date} {recurring_end}"
                })
            
            response = requests.post(
                f'http://web-api:4000/l/listings/{selected_listing_id}/availability',
                json={'slots': slots}
            )
            
            if response.status_code == 201:
                st.success(f"✅ Added {num_weeks} recurring slots!")
                st.rerun()
            else:
                st.error(f"Failed to add availability: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()

# VIEW EXISTING AVAILABILITY
st.subheader("3️⃣ Current Availability")

try:
    availability_response = requests.get(
        f'http://web-api:4000/l/listings/{selected_listing_id}/availability'
    )
    
    if availability_response.status_code == 200:
        availability_data = availability_response.json()
        
        if len(availability_data) == 0:
            st.info("No availability slots set for this service yet.")
        else:
            st.write(f"**{len(availability_data)}** availability slot(s)")
            
            # Display in a table-like format
            for slot in availability_data:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"📅 {slot['startTime']}")
                with col2:
                    st.write(f"🕐 Start: {slot['startTime']}")
                with col3:
                    st.write(f"🕐 End: {slot['endTime']}")
                with col4:
                    if st.button("🗑️", key=f"delete_{slot['availabilityId']}", help="Delete"):
                        try:
                            delete_response = requests.delete(
                                f'http://web-api:4000/l/listings/{selected_listing_id}/availability/{slot["availabilityId"]}'
                            )
                            if delete_response.status_code == 200:
                                st.success("Deleted!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                st.divider()
    else:
        st.warning("Could not load availability. Make sure the GET availability route is implemented.")
        
except Exception as e:
    st.error(f"Error: {str(e)}")

# Navigation
st.divider()
if st.button("🏠 Back to Dashboard", use_container_width=True):
    st.switch_page("pages/20_Jessica_Provider_Home.py")
