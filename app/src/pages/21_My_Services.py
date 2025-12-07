import streamlit as st
import requests
from modules.nav import SideBarLinks

st.set_page_config(page_title="My Services", page_icon="📝", layout="wide")
SideBarLinks()

st.title("📝 My Services")
st.write("Manage your service offerings")

# Set provider ID (change to match your database)
provider_id = 3

st.divider()

# ADD NEW SERVICE SECTION
with st.expander("➕ Add New Service"):
    with st.form("add_service_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Service Title*", placeholder="e.g., Calculus Tutoring")
            category_id = st.number_input("Category ID*", min_value=1, value=1, 
                                         help="1=Tutoring, 2=Moving, 3=Marketplace, 4=Tech")
            price = st.number_input("Price*", min_value=0.0, value=25.0, step=5.0)
        
        with col2:
            unit = st.selectbox("Unit*", ["per hour", "per session", "flat rate", "per item"])
            description = st.text_area("Description*", 
                                      placeholder="Describe your service...",
                                      height=100)
        
        image_url = st.text_input("Image URL (optional)", 
                                  placeholder="https://example.com/image.jpg")
        
        submit = st.form_submit_button("Create Service", use_container_width=True)
        
        if submit:
            if not title or not description:
                st.error("Please fill in all required fields")
            else:
                try:
                    response = requests.post(
                        'http://web-api:4000/l/listings',
                        json={
                            'categoryId': category_id,
                            'providerId': provider_id,
                            'title': title,
                            'description': description,
                            'price': price,
                            'unit': unit,
                            'imageUrl': image_url
                        }
                    )
                    
                    if response.status_code == 201:
                        st.success("✅ Service created successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create service: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

st.divider()

# DISPLAY EXISTING SERVICES
st.subheader("📋 Your Services")

# Filter options
col1, col2 = st.columns([3, 1])
with col1:
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "active", "inactive", "removed"]
    )

try:
    response = requests.get(f'http://web-api:4000/l/listings')
    
    if response.status_code == 200:
        all_listings = response.json()
        
        # Filter by provider and status
        my_listings = [l for l in all_listings if l.get('providerId') == provider_id]
        
        if status_filter != "All":
            my_listings = [l for l in my_listings if l.get('listingStatus') == status_filter]
        
        if len(my_listings) == 0:
            st.info("No services found. Create your first service above!")
        else:
            st.write(f"Showing **{len(my_listings)}** service(s)")
            
            # Display each service as a card
            for listing in my_listings:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"### {listing['title']}")
                        st.write(listing['description'][:150] + "..." if len(listing['description']) > 150 else listing['description'])
                        st.caption(f"💵 ${listing['price']:.2f} {listing['unit']} | Status: {listing['listingStatus']}")
                    
                    with col2:
                        # Edit button - show form in expander
                        if st.button("✏️ Edit", key=f"edit_{listing['listingId']}", use_container_width=True):
                            st.session_state[f'editing_{listing["listingId"]}'] = True
                    
                    with col3:
                        # Delete button
                        if st.button("🗑️ Remove", key=f"delete_{listing['listingId']}", use_container_width=True):
                            try:
                                delete_response = requests.delete(
                                    f'http://web-api:4000/l/listings/{listing["listingId"]}'
                                )
                                if delete_response.status_code == 200:
                                    st.success("Service removed!")
                                    st.rerun()
                                else:
                                    st.error("Failed to remove service")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    # Edit form (shows if edit button was clicked)
                    if st.session_state.get(f'editing_{listing["listingId"]}', False):
                        with st.form(f"edit_form_{listing['listingId']}"):
                            new_price = st.number_input("New Price", value=float(listing['price']), min_value=0.0)
                            new_description = st.text_area("New Description", value=listing['description'])
                            
                            col_save, col_cancel = st.columns(2)
                            with col_save:
                                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                    try:
                                        update_response = requests.put(
                                            f'http://web-api:4000/l/listings/{listing["listingId"]}',
                                            json={
                                                'price': new_price,
                                                'description': new_description
                                            }
                                        )
                                        if update_response.status_code == 200:
                                            st.success("Updated!")
                                            st.session_state[f'editing_{listing["listingId"]}'] = False
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            with col_cancel:
                                if st.form_submit_button("❌ Cancel", use_container_width=True):
                                    st.session_state[f'editing_{listing["listingId"]}'] = False
                                    st.rerun()
                    
                    st.divider()
    else:
        st.error(f"Failed to load services: {response.status_code}")
        
except Exception as e:
    st.error(f"Error: {str(e)}")