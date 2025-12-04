import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(page_title="Pending Requests", page_icon="📋", layout="wide")
SideBarLinks()

st.title("📋 Pending Service Requests")
st.write("Review and respond to booking requests")

# Set provider ID
provider_id = 3

st.divider()

# FILTERS
col1, col2 = st.columns([2, 1])
with col1:
    st.write("### Filter Requests")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# DISPLAY PENDING REQUESTS
try:
    response = requests.get(
        f'http://api:4000/t/transactions',
        params={'providerId': provider_id, 'status': 'requested'}
    )
    
    if response.status_code == 200:
        requests_data = response.json()
        
        if len(requests_data) == 0:
            st.info("🎉 No pending requests! All caught up.")
        else:
            st.write(f"You have **{len(requests_data)}** pending request(s)")
            st.write("")
            
            # Display each request
            for idx, req in enumerate(requests_data):
                with st.container():
                    # Header with request number
                    st.write(f"#### Request #{idx + 1}")
                    
                    # Main info in columns
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Service:** {req[4]}")  # service_name
                        st.write(f"**Student:** {req[7]}")  # student_name
                        st.write(f"**Email:** {req[8]}")    # student_email
                        st.write(f"**Phone:** {req[9]}")    # student_phone
                        
                        if req[10]:  # agreementDetails
                            st.write(f"**Notes:** {req[10]}")
                    
                    with col2:
                        st.metric("💰 Payment", f"${req[3]:.2f}")
                        st.write(f"**Date:** {req[1]}")
                        st.write(f"**Status:** {req[2]}")
                    
                    # Action buttons
                    st.write("")
                    col_accept, col_decline, col_space = st.columns([1, 1, 2])
                    
                    with col_accept:
                        if st.button(
                            "✅ Accept Request",
                            key=f"accept_{req[0]}",
                            use_container_width=True,
                            type="primary"
                        ):
                            try:
                                update_response = requests.put(
                                    f'http://api:4000/t/transactions/{req[0]}',
                                    json={'transactStatus': 'confirmed'}
                                )
                                if update_response.status_code == 200:
                                    st.success("✅ Request accepted!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("Failed to accept request")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col_decline:
                        if st.button(
                            "❌ Decline Request",
                            key=f"decline_{req[0]}",
                            use_container_width=True
                        ):
                            try:
                                update_response = requests.put(
                                    f'http://api:4000/t/transactions/{req[0]}',
                                    json={'transactStatus': 'cancelled'}
                                )
                                if update_response.status_code == 200:
                                    st.warning("Request declined")
                                    st.rerun()
                                else:
                                    st.error("Failed to decline request")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    st.divider()
    else:
        st.error(f"Failed to load requests: {response.status_code}")
        
except Exception as e:
    st.error(f"Error connecting to API: {str(e)}")

# Quick navigation
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/20_Jessica_Provider_Home.py")
with col2:
    if st.button("📝 Manage Services", use_container_width=True):
        st.switch_page("pages/21_My_Services.py")