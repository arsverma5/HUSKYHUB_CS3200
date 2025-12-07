import streamlit as st
import requests
from modules.nav import SideBarLinks

# Page configuration
st.set_page_config(
    page_title="Provider Dashboard",
    page_icon="📊",
    layout="wide"
)

# Sidebar navigation
SideBarLinks()

# Page title
st.title("📊 Provider Dashboard")
st.write("### Welcome back, Jessica!")

# Set Jessica's provider ID (change to match your database)
provider_id = 3

st.divider()

# ==========================================
# SECTION 1: Performance Metrics
# ==========================================
st.subheader("💼 Your Performance")

try:
    # Call the metrics API
    response = requests.get(f'http://web-api:4000/students/{provider_id}/metrics')
    
    if response.status_code == 200:
        data = response.json()
        
        # Create 4 columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Earnings",
                value=f"${float(data['total_earnings']):,.2f}"
            )
        
        with col2:
            st.metric(
                label="✅ Completed Bookings",
                value=data['completed_bookings']
            )
        
        with col3:
            rating_value = float(data['average_rating']) if data['average_rating'] else 0
            st.metric(
                label="⭐ Average Rating",
                value=f"{rating_value:.1f}/5.0" if rating_value > 0 else "No ratings yet"
            )
        
        with col4:
            st.metric(
                label="📊 Total Services",
                value=data['total_services_offered']
            )
    else:
        st.error(f"Failed to load metrics: {response.status_code}")
        st.write(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to API: {str(e)}")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")

st.divider()

# ==========================================
# SECTION 2: Pending Requests
# ==========================================
st.subheader("📋 Pending Service Requests")

try:
    # Call the pending requests API
    response = requests.get(
        f'http://web-api:4000/transactions',
        params={'providerId': provider_id, 'status': 'requested'}
    )
    
    if response.status_code == 200:
        requests_data = response.json()
        
        if len(requests_data) == 0:
            st.info("🎉 No pending requests at the moment!")
        else:
            st.write(f"You have **{len(requests_data)}** pending request(s)")
            st.write("")
            
            # Show each request
            for req in requests_data[:5]:  # Show top 5
                with st.container():
                    # Create columns for request info and actions
                    col1, col2, col3 = st.columns([4, 1, 1])
                    
                    with col1:
                        st.write(f"**{req[4]}**")  # service_name
                        st.caption(
                            f"👤 {req[7]} | "  # student_name
                            f"📅 {str(req[1])} | "  # bookDate
                            f"💵 ${float(req[3]):,.2f}"  # paymentAmt
                        )
                    
                    with col2:
                        if st.button("✅ Accept", key=f"accept_{req[0]}", use_container_width=True):
                            try:
                                update_response = requests.put(
                                    f'http://web-api:4000/transactions/{req[0]}',
                                    json={'transactStatus': 'confirmed'}
                                )
                                if update_response.status_code == 200:
                                    st.success("✅ Request accepted!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"Failed to accept: {update_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col3:
                        if st.button("❌ Decline", key=f"decline_{req[0]}", use_container_width=True):
                            try:
                                update_response = requests.put(
                                    f'http://web-api:4000/transactions/{req[0]}',
                                    json={'transactStatus': 'cancelled'}
                                )
                                if update_response.status_code == 200:
                                    st.warning("Request declined")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to decline: {update_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    st.divider()
            
            # Button to see all requests
            if len(requests_data) > 5:
                if st.button("📋 View All Pending Requests"):
                    st.switch_page("pages/22_Pending_Requests.py")
    else:
        st.error(f"Failed to load requests: {response.status_code}")
        st.write(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to API: {str(e)}")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")

st.divider()

# ==========================================
# SECTION 3: Quick Actions
# ==========================================
st.subheader("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📝 Manage My Services", use_container_width=True):
        st.switch_page("pages/21_My_Services.py")

with col2:
    if st.button("📅 Set Availability", use_container_width=True):
        st.switch_page("pages/23_My_Availability.py")

with col3:
    if st.button("📋 All Requests", use_container_width=True):
        st.switch_page("pages/22_Pending_Requests.py")