import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title('📅 My Bookings')
st.write(f"Manage your service appointments, {st.session_state['first_name']}")

API_URL = "http://web-api:4000"
user_id = st.session_state.get('user_id', 1)

tab1, tab2, tab3 = st.tabs(["Pending", "Confirmed", "Completed"])

try:
    # Get Emma's transactions (User Story 1.3)
    response = requests.get(f'{API_URL}/transactions/?buyerId={user_id}')
    
    if response.status_code == 200:
        all_bookings = response.json()
        
        pending_bookings = [b for b in all_bookings if b.get('transactStatus') == 'requested']
        confirmed_bookings = [b for b in all_bookings if b.get('transactStatus') == 'confirmed']
        completed_bookings = [b for b in all_bookings if b.get('transactStatus') == 'completed']
        
        with tab1:
            if pending_bookings:
                for booking in pending_bookings:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.subheader(booking.get('service_name', 'Service'))
                            st.write(f"**Provider:** {booking.get('provider_name', 'Unknown')}")
                            st.write(f"**Date:** {booking.get('bookDate', 'TBD')}")
                        
                        with col2:
                            st.metric("Amount", f"${booking.get('paymentAmt', 0)}")
                        
                        with col3:
                            if st.button("Cancel", key=f"cancel_{booking['transactId']}"):
                                # Call DELETE endpoint
                                cancel_response = requests.delete(
                                    f"{API_URL}/transactions/{booking['transactId']}"
                                )
                                if cancel_response.status_code == 200:
                                    st.success("Booking cancelled!")
                                    st.rerun()
                        
                        st.write('---')
            else:
                st.info('No pending bookings')
        
        with tab2:
            if confirmed_bookings:
                for booking in confirmed_bookings:
                    st.write(f"**{booking.get('service_name')}** - {booking.get('bookDate')}")
                    st.write(f"Provider: {booking.get('provider_name')}")
                    st.write(f"Amount: ${booking.get('paymentAmt')}")
                    st.write('---')
            else:
                st.info('No confirmed bookings')
        
        with tab3:
            if completed_bookings:
                for booking in completed_bookings:
                    st.write(f"**{booking.get('service_name')}** - {booking.get('fulfillmentDate')}")
                    st.write(f"Provider: {booking.get('provider_name')}")
                    st.write(f"Amount: ${booking.get('paymentAmt')}")
                    
                    # Option to leave review (User Story 1.4)
                    if st.button("Leave a Review", key=f"review_{booking['transactId']}"):
                        st.session_state['review_booking_id'] = booking['transactId']
                        st.session_state['review_listing_id'] = booking.get('listId')
                        st.info("Review feature coming soon!")
                    
                    st.write('---')
            else:
                st.info('No completed bookings')
    else:
        st.error('Failed to load bookings')
        
except requests.exceptions.RequestException as e:
    st.error(f'Error connecting to API: {str(e)}')