import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("Listing Management")

# API URL
API_URL = "http://web-api:4000"

# Initialize session state
if "listing_active_tab" not in st.session_state:
    st.session_state.listing_active_tab = "View All Listings"
if "selected_listing" not in st.session_state:
    st.session_state.selected_listing = None
if "search_listing_id_value" not in st.session_state:
    st.session_state.search_listing_id_value = 1
if "show_listing_edit_form" not in st.session_state:
    st.session_state.show_listing_edit_form = False

# Check if coming from Reports page
if "search_listing_id" in st.session_state and st.session_state.search_listing_id is not None:
    listing_id = st.session_state.search_listing_id
    st.session_state.search_listing_id = None
    st.session_state.search_listing_id_value = listing_id
    st.session_state.listing_active_tab = "Search For Listing"
    st.session_state.show_listing_edit_form = False
    
    try:
        response = requests.get(f"{API_URL}/listings/{listing_id}")
        if response.status_code == 200:
            st.session_state.selected_listing = response.json()
    except Exception as e:
        st.error(f"Could not fetch listing details: {e}")

# Tabs - order changes based on active_tab
if st.session_state.listing_active_tab == "Search For Listing":
    tab2, tab1 = st.tabs(["Search For Listing", "View All Listings"])
else:
    tab1, tab2 = st.tabs(["View All Listings", "Search For Listing"])


# ============================================================
# SEARCH FOR LISTING TAB
# ============================================================
with tab2:
    st.subheader("Search For Listing")
    
    # Search bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_id = st.number_input(
            "Enter Listing ID", 
            min_value=1, 
            step=1, 
            value=st.session_state.search_listing_id_value,
            key="listing_search_id_input",
            label_visibility="collapsed"
        )
    with col2:
        search_clicked = st.button("🔍 Search", key="listing_search_btn", use_container_width=True)
    
    if search_clicked:
        try:
            response = requests.get(f"{API_URL}/listings/{search_id}")
            if response.status_code == 200:
                st.session_state.selected_listing = response.json()
                st.session_state.search_listing_id_value = search_id
                st.session_state.show_listing_edit_form = False
                st.rerun()
            else:
                st.warning(f"Listing #{search_id} not found")
                st.session_state.selected_listing = None
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to API: {e}")
    
    # Clear button
    if st.session_state.selected_listing is not None:
        if st.button("✖ Clear Search", key="listing_clear_search_btn"):
            st.session_state.selected_listing = None
            st.session_state.listing_active_tab = "View All Listings"
            st.session_state.show_listing_edit_form = False
            st.rerun()
    
    # Display selected listing details
    if st.session_state.selected_listing is not None:
        st.divider()
        
        listing = st.session_state.selected_listing
        
        st.subheader(f"{listing.get('title')}")
        
        # Status badge
        status = listing.get('listingStatus', 'active')
        if status == 'removed':
            st.error("Status: Removed")
        elif status == 'active':
            st.success("Status: Active")
        else:
            st.info(f"Status: {status}")
        
        # Listing info columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Listing Info**")
            st.write(f"**ID:** {listing.get('listingId')}")
            st.write(f"**Title:** {listing.get('title')}")
            st.write(f"**Category:** {listing.get('category_name')}")
            st.write(f"**Price:** ${listing.get('price')} / {listing.get('unit')}")
            last_update = listing.get('lastUpdate')
            if last_update:
                st.write(f"**Last Updated:** {str(last_update)[:10]}")
        
        with col2:
            st.markdown("**Provider Info**")
            st.write(f"**Provider ID:** {listing.get('provider_id')}")
            st.write(f"**Name:** {listing.get('provider_name')}") 
            st.write(f"**Email:** {listing.get('provider_email', 'N/A')}")
            st.write(f"**Verified:** {'✅' if listing.get('provider_verified') else '❌'}")
        
        # Description
        st.divider()
        st.markdown("**Description**")
        st.write(listing.get('description', 'No description'))
        
        # Stats
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Reviews", listing.get('review_count', 0))
        with col2:
            avg_rating = listing.get('avg_rating') or 0
            st.metric("Avg Rating", f"⭐ {avg_rating}")
        
        # Action buttons
        st.divider()
        st.markdown("**⚡ Admin Actions**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status == 'active':
                if st.button("Remove Listing", use_container_width=True, key="listing_remove_btn"):
                    try:
                        resp = requests.delete(f"{API_URL}/listings/{listing.get('listingId')}")
                        if resp.status_code == 200:
                            st.success("Listing removed!")
                            st.session_state.selected_listing = None
                            st.rerun()
                        else:
                            st.error("Failed to remove listing")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
            else:
                if st.button("Reactivate Listing", use_container_width=True, key="listing_reactivate_btn"):
                    try:
                        resp = requests.put(
                            f"{API_URL}/listings/{listing.get('listingId')}",
                            json={"listingStatus": "active"}
                        )
                        if resp.status_code == 200:
                            st.success("Listing reactivated!")
                            st.session_state.selected_listing = None
                            st.rerun()
                        else:
                            st.error("Failed to reactivate listing")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
        
        with col2:
            if st.button("Edit Listing", use_container_width=True, key="listing_edit_btn"):
                st.session_state.show_listing_edit_form = True
                st.rerun()
        
        with col3:
            if st.button("View Provider", use_container_width=True, key="listing_view_provider_btn"):
                st.session_state.search_user_id = listing.get('provider_id')
                st.switch_page("pages/32_User_Management.py")
        
        # Edit Form
        if st.session_state.show_listing_edit_form:
            st.divider()
            st.subheader("Edit Listing")
            
            with st.form("listing_edit_form"):
                new_price = st.number_input(
                    "Price",
                    min_value=0.0,
                    value=float(listing.get('price', 0)),
                    step=0.01
                )
                
                new_description = st.text_area(
                    "Description",
                    value=listing.get('description', ''),
                    height=150
                )
                
                col_submit, col_cancel = st.columns(2)
                
                with col_submit:
                    submit = st.form_submit_button("Save Changes", use_container_width=True)
                with col_cancel:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)
                
                if submit:
                    try:
                        payload = {
                            "price": new_price,
                            "description": new_description
                        }
                        
                        resp = requests.put(
                            f"{API_URL}/listings/{listing.get('listingId')}",
                            json=payload
                        )
                        
                        if resp.status_code == 200:
                            st.success("Listing updated successfully!")
                            st.session_state.show_listing_edit_form = False
                            st.session_state.selected_listing = None
                            st.rerun()
                        else:
                            st.error(f"Error: {resp.json().get('error', 'Unknown error')}")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
                
                if cancel:
                    st.session_state.show_listing_edit_form = False
                    st.rerun()


# ============================================================
# VIEW ALL LISTINGS TAB
# ============================================================
with tab1:
    st.subheader("View All Listings")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["", "active", "removed"],
            key="listing_status_filter_select",
            format_func=lambda x: "All" if x == "" else x.capitalize()
        )
    
    with col2:
        # Fetch categories for dropdown
        try:
            cat_response = requests.get(f"{API_URL}/listings/categories")
            if cat_response.status_code == 200:
                categories = cat_response.json()
                category_options = [""] + [str(c.get('categoryId')) for c in categories]
                category_names = {str(c.get('categoryId')): c.get('name') for c in categories}
                category_names[""] = "All Categories"
                
                category_filter = st.selectbox(
                    "Filter by Category",
                    category_options,
                    key="listing_category_filter_select",
                    format_func=lambda x: category_names.get(x, x)
                )
            else:
                category_filter = ""
                st.warning("Could not load categories")
        except:
            category_filter = ""
    
    with col3:
        search_term = st.text_input("Search", placeholder="Title or description...", key="listing_text_search_input")
    
    try:
        # Build query params
        params = {}
        if status_filter:
            params["status"] = status_filter
        if category_filter:
            params["categoryId"] = category_filter
        if search_term:
            params["search"] = search_term
        
        response = requests.get(f"{API_URL}/listings", params=params)
        
        if response.status_code == 200:
            listings = response.json()
            
            if len(listings) == 0:
                st.info("No listings found.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Listings", len(listings))
                with col2:
                    active_count = sum(1 for l in listings if l.get("listingStatus") == "active")
                    st.metric("Active", active_count)
                with col3:
                    removed_count = sum(1 for l in listings if l.get("listingStatus") == "removed")
                    st.metric("Removed", removed_count)
                
                st.divider()
                
                # Display listing cards
                for listing in listings:
                    listing_id = listing.get("listingId")
                    title = listing.get("title", "Untitled")
                    category = listing.get("category_name", "N/A")
                    price = listing.get("price", 0)
                    unit = listing.get("unit", "")
                    status = listing.get("listingStatus", "active")
                    provider_name = listing.get("provider_name", "N/A")
                    provider_verified = listing.get("provider_verified", False)
                    
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**#{listing_id}**")
                            if status == "removed":
                                st.error("Removed")
                            else:
                                st.success("Active")
                        
                        with col2:
                            st.write(f"**{title}**")
                            st.write(f"**Category:** {category}")
                            st.write(f"**Price:** ${price} / {unit}")
                        
                        with col3:
                            st.write(f"**Provider:** {provider_name}")
                            if not provider_verified:
                                st.warning("Unverified Provider")
                        
                        with col4:
                            if st.button("View", key=f"listing_view_card_{listing_id}", use_container_width=True):
                                st.session_state.search_listing_id_value = listing_id
                                st.session_state.listing_active_tab = "Search For Listing"
                                st.session_state.show_listing_edit_form = False
                                
                                fetch_success = False
                                try:
                                    resp = requests.get(f"{API_URL}/listings/{listing_id}")
                                    if resp.status_code == 200:
                                        st.session_state.selected_listing = resp.json()
                                        fetch_success = True
                                    else:
                                        st.error(f"Listing not found: {resp.status_code}")
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Could not fetch listing: {e}")
                                
                                if fetch_success:
                                    st.rerun()
        else:
            st.error(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to API: {e}")