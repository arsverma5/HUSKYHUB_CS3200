import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

# Get the selected listing from session state or query params
if 'selected_listing_id' not in st.session_state:
    st.session_state['selected_listing_id'] = 1  # Default to first listing

listing_id = st.session_state['selected_listing_id']

st.title('Provider Profile & Service Details')

API_URL = "http://web-api:4000"

try:
    # Get listing details
    listing_response = requests.get(f'{API_URL}/listings/{listing_id}')
    
    if listing_response.status_code == 200:
        listing = listing_response.json()
        
        # Provider info section (User Story 1.2)
        provider_id = listing.get('providerId')
        
        if provider_id:
            # Get provider profile
            provider_response = requests.get(f'{API_URL}/students/{provider_id}')
            
            if provider_response.status_code == 200:
                provider = provider_response.json()
                
                # Display provider info
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.header(f"{provider.get('firstName')} {provider.get('lastName')}")
                    
                    if provider.get('verifiedStatus'):
                        st.success("✅ Verified NEU Student")
                    
                    st.write(f"**Major:** {provider.get('major', 'Not specified')}")
                    st.write(f"**Email:** {provider.get('email')}")
                    st.write(f"**Bio:** {provider.get('bio', 'No bio available')}")
                    
                    # Service details
                    st.write('---')
                    st.subheader('Service Details')
                    st.write(f"**{listing.get('title')}**")
                    st.write(listing.get('description'))
                    st.write(f"**Price:** ${listing.get('price')}/{listing.get('unit')}")
                
                with col2:
                    # Metrics
                    st.metric("Total Services", provider.get('total_services', 0))
                    
                    avg_rating = provider.get('avg_rating')
                    if avg_rating:
                        st.metric("Average Rating", f"⭐ {float(avg_rating):.1f}")
                    else:
                        st.metric("Average Rating", "No ratings yet")
                    
                    st.metric("Total Reviews", provider.get('total_reviews', 0))
                
                # Reviews section (User Story 1.4)
                st.write('---')
                st.subheader('📝 Reviews')
                
                reviews_response = requests.get(f'{API_URL}/listings/{listing_id}/reviews')
                
                if reviews_response.status_code == 200:
                    reviews = reviews_response.json()
                    
                    if reviews:
                        for review in reviews:
                            with st.container():
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(f"**{review.get('reviewer_name', 'Anonymous')}**")
                                    st.write(review.get('reviewText', ''))
                                
                                with col2:
                                    st.write(f"⭐ {review.get('rating')}/5")
                                    st.caption(review.get('createDate', ''))
                                
                                st.write('---')
                    else:
                        st.info('No reviews yet')
                
                # Availability section (User Story 1.3)
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
                                if st.button(f"Book This Slot", key=f"book_{slot['availabilityId']}"):
                                    st.session_state['selected_slot'] = slot
                                    st.session_state['selected_listing'] = listing
                                    st.success("Booking functionality coming soon!")
                    else:
                        st.info('No availability posted yet')
            
    else:
        st.error('Failed to load listing details')
        
except requests.exceptions.RequestException as e:
    st.error(f'Error connecting to API: {str(e)}')