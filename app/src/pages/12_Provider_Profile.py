import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

if 'selected_listing_id' not in st.session_state:
    st.session_state['selected_listing_id'] = 1 

listing_id = st.session_state['selected_listing_id']

st.title('Provider Profile & Service Details')

API_URL = "http://web-api:4000"

try:
    # Get listing details (includes provider info)
    listing_response = requests.get(f'{API_URL}/listings/{listing_id}')
    
    if listing_response.status_code == 200:
        listing = listing_response.json()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header(listing.get('provider_name', 'Unknown Provider'))
            
            if listing.get('provider_verified'):
                st.success("✅ Verified NEU Student")
            
            st.write(f"**Email:** {listing.get('provider_email', 'Not provided')}")
            st.write(f"**Phone:** {listing.get('provider_phone', 'Not provided')}")
            st.write(f"**Bio:** {listing.get('provider_bio', 'No bio available')}")
            
            # Service details
            st.write('---')
            st.subheader('Service Details')
            st.write(f"**{listing.get('title')}**")
            st.write(listing.get('description'))
            st.write(f"**Price:** ${listing.get('price')}/{listing.get('unit')}")
            st.write(f"**Category:** {listing.get('category_name')}")
        
        with col2:
            # Metrics from listing
            avg_rating = listing.get('avg_rating')
            if avg_rating:
                st.metric("Average Rating", f"⭐ {float(avg_rating):.1f}")
            else:
                st.metric("Average Rating", "No ratings yet")
            
            st.metric("Total Reviews", listing.get('review_count', 0))
        
        # Reviews section
        st.write('---')
        st.subheader('Reviews')
        
        reviews_response = requests.get(f'{API_URL}/listings/{listing_id}/reviews')
        
        if reviews_response.status_code == 200:
            reviews = reviews_response.json()
            
            if reviews:
                for review in reviews:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{review.get('reviewer_name', 'Anonymous')}**")
                            if review.get('reviewer_verified'):
                                st.caption("✅ Verified Student")
                            st.write(review.get('reviewText', ''))
                        
                        with col2:
                            st.write(f"⭐ {review.get('rating')}/5")
                            st.caption(review.get('createDate', ''))
                        
                        st.divider()
            else:
                st.info('No reviews yet for this service')
        
        # Availability section
        st.write('---')
        st.subheader('📅 Available Time Slots')
        
        availability_response = requests.get(f'{API_URL}/listings/{listing_id}/availability')
        
        if availability_response.status_code == 200:
            slots = availability_response.json()
            
            if slots:
                for slot in slots[:5]:  # Show first 5 slots
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"📅 {slot.get('startTime')} - {slot.get('endTime')}")
                    
                    with col2:
                        if st.button(f"Book This Slot", key=f"book_{slot.get('availabilityId')}"):
                            st.session_state['selected_slot'] = slot
                            st.session_state['selected_listing'] = listing
                            st.success("Booking functionality coming soon!")
            else:
                st.info('No availability posted yet')
        else:
            st.info('No availability information available')
    else:
        st.error(f'Failed to load listing details: {listing_response.status_code}')
        
except requests.exceptions.RequestException as e:
    st.error(f'Error connecting to API: {str(e)}')