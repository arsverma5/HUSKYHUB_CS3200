import logging
logger = logging.getLogger(__name__)

import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(layout='wide')
SideBarLinks()

st.title('🔍 Browse Services')
st.write('Find trusted student services on campus')

API_URL = "http://web-api:4000"

st.write('### Search & Filter')

col1, col2, col3 = st.columns(3)

with col1:
    # Category filter (User Story 1.1)
    category = st.selectbox(
        'Category',
        ['All', 'Tutoring', 'Moving Help', 'Marketplace', 'Tech Help']
    )

with col2:
    search_term = st.text_input('Search by keyword')

with col3:
    # Sort by (User Story 1.5 - compare prices)
    sort_by = st.selectbox(
        'Sort by',
        ['Price (Low to High)', 'Price (High to Low)', 'Rating (High to Low)']
    )

params = {}
if category != 'All':
    params['category'] = category
if search_term:
    params['q'] = search_term

# Call listings API (User Story 1.1, 1.5)
try:
    response = requests.get(f'{API_URL}/listings/', params=params)
    
    if response.status_code == 200:
        listings = response.json()
        
        if 'Price (Low' in sort_by:
            listings.sort(key=lambda x: x.get('price', 999))
        elif 'Price (High' in sort_by:
            listings.sort(key=lambda x: x.get('price', 0), reverse=True)
        elif 'Rating' in sort_by:
            listings.sort(key=lambda x: x.get('avg_rating', 0) or 0, reverse=True)
        
        st.write(f'### Found {len(listings)} services')
        st.write('---')
        
        for listing in listings:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(listing.get('title', 'Untitled'))
                    st.write(f"**Provider:** {listing.get('provider_name', 'Unknown')}")
                    if listing.get('verifiedStatus'):
                        st.markdown("**Verified NEU Student**")
                    st.write(listing.get('description', '')[:150] + '...')
                
                with col2:
                    st.metric("Price", f"${listing.get('price', 0)}/{listing.get('unit', 'hour')}")
                    rating = listing.get('avg_rating')
                    if rating:
                        st.metric("Rating", f"{float(rating):.1f}")
                    else:
                        st.metric("Rating", "No reviews")
                
                with col3:
                    review_count = listing.get('review_count', 0)
                    st.write(f"{review_count} reviews")
                    
                    # Button to view details
                    if st.button(f"View Details", key=f"view_{listing['listingId']}"):
                        st.session_state['selected_listing_id'] = listing['listingId']
                        st.switch_page('pages/12_Provider_Profile.py')
                
                st.write('---')
    else:
        st.error('Failed to load services')
        
except requests.exceptions.RequestException as e:
    st.error(f'Error connecting to API: {str(e)}')
    st.info('Please ensure the API server is running')