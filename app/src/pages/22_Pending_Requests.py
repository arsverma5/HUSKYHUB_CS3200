import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(page_title="Pending Requests", page_icon="📋", layout="wide")
SideBarLinks()

st.title("📋 Pending Service Requests")
st.write("Review and respond to booking requests")

provider_id = 3

st.divider()

# ==========================================
# FILTERS
# ==========================================
col1, col2 = st.columns([2, 1])
with col1:
    st.write("### Filter Requests")
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.divider()

# ==========================================
# DISPLAY PENDING REQUESTS
# ==========================================
try:
    # FIXED: Use /transactions (not /t/transactions)
    response = requests.get(
        f'http://web-api:4000/transactions',
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
                    st.write(f"#### Request #{idx + 1}")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Service:** {req['service_name']}")
                        st.write(f"**Student:** {req['buyer_name']}")
                        st.write(f"**Email:** {req['buyer_email']}")
                        st.write(f"**Phone:** {req['buyer_phone']}")
                        
                        if req['agreementDetails']:
                            st.write(f"**Notes:** {req['agreementDetails']}")
                    
                    with col2:
                        st.metric("💰 Payment", f"${float(req['paymentAmt']):,.2f}")
                        st.write(f"**Date:** {req['bookDate']}")
                        st.write(f"**Status:** {req['transactStatus']}")
                    
                    st.write("")
                    col_accept, col_decline, col_space = st.columns([1, 1, 2])
                    
                    with col_accept:
                        if st.button(
                            "✅ Accept Request",
                            key=f"accept_{req['transactId']}",
                            use_container_width=True,
                            type="primary"
                        ):
                            try:
                                update_response = requests.put(
                                    f'http://web-api:4000/transactions/{req["transactId"]}',
                                    json={'transactStatus': 'confirmed'}
                                )
                                if update_response.status_code == 200:
                                    st.success("✅ Request accepted!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {update_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col_decline:
                        if st.button(
                            "❌ Decline Request",
                            key=f"decline_{req['transactId']}",
                            use_container_width=True
                        ):
                            try:
                                update_response = requests.put(
                                    f'http://web-api:4000/transactions/{req["transactId"]}',
                                    json={'transactStatus': 'cancelled'}
                                )
                                if update_response.status_code == 200:
                                    st.warning("Request declined")
                                    st.rerun()
                                else:
                                    st.error(f"Failed: {update_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    st.divider()
    else:
        st.error(f"Failed to load requests: {response.status_code}")
        st.write(f"Response: {response.text}")
        
except Exception as e:
    st.error(f"Error: {str(e)}")

# Quick navigation
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/20_Jessica_Provider_Home.py")
with col2:
    if st.button("📝 Manage Services", use_container_width=True):
        st.switch_page("pages/21_My_Services.py")