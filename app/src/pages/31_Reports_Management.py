import streamlit as st
import requests
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("Reports Dashboard")

# API URL
API_URL = "http://web-api:4000"

# Initialize session state for search results/resolve form
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "show_resolve_form" not in st.session_state:
    st.session_state.show_resolve_form = False

# search section
st.subheader("🔍 Search Report by ID")

col1, col2 = st.columns([3, 1])
with col1:
    report_id = st.number_input("Enter Report ID", min_value=1, step=1, value=1, label_visibility="collapsed")
with col2:
    search_clicked = st.button("🔍 Search", use_container_width=True)

if search_clicked:
    try:
        response = requests.get(f"{API_URL}/admin/reports/{report_id}")
        
        if response.status_code == 200:
            st.session_state.search_result = response.json()
        elif response.status_code == 404:
            st.session_state.search_result = "not_found"
        else:
            st.session_state.search_result = "error"
            
    except requests.exceptions.ConnectionError:
        st.session_state.search_result = "connection_error"

# Clear search button
if st.session_state.search_result is not None:
    if st.button("✖ Clear Search"):
        st.session_state.search_result = None
        st.rerun()

# display search results
if st.session_state.search_result is not None:
    st.divider()
    
    if st.session_state.search_result == "not_found":
        st.warning(f"⚠️ Report #{report_id} not found")
    elif st.session_state.search_result == "connection_error":
        st.error("❌ Could not connect to API. Make sure Flask is running.")
    elif st.session_state.search_result == "error":
        st.error("❌ An error occurred")
    else:
        report = st.session_state.search_result
        
        st.subheader(f"📄 Report #{report.get('reportId')} Details")
        
        # Priority badge
        priority = report.get("priority", "MEDIUM")
        if priority == "URGENT":
            st.error(f"🔴 Priority: {priority}")
        elif priority == "HIGH":
            st.warning(f"🟠 Priority: {priority}")
        else:
            st.info(f"🔵 Priority: {priority}")
        
        # Report info in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Report Information**")
            st.write(f"**Report ID:** {report.get('reportId')}")
            st.write(f"**Date:** {report.get('reportDate')}")
            st.write(f"**Reason:** {report.get('reason')}")
            st.write(f"**Details:** {report.get('reportDetails') or 'N/A'}")
            st.write(f"**Resolution:** {report.get('resolutionDate') or 'Pending'}")
        
        with col2:
            st.markdown("**👤 Reporter**")
            st.write(f"**Name:** {report.get('reporter_fname')} {report.get('reporter_lname')}")
            st.write(f"**Email:** {report.get('reporter_email')}")
            st.write(f"**Status:** {report.get('reporter_account_status')}")
        
        st.divider()
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**🚨 Reported Student**")
            st.write(f"**Name:** {report.get('reported_fname')} {report.get('reported_lname')}")
            st.write(f"**Email:** {report.get('reported_email')}")
            st.write(f"**Status:** {report.get('reported_account_status')}")
        
        with col4:
            if report.get('reported_listing_id'):
                st.markdown("**📦 Reported Listing**")
                st.write(f"**Title:** {report.get('listing_title')}")
                st.write(f"**Status:** {report.get('listingStatus')}")
                st.write(f"**Category:** {report.get('category_name')}")
            else:
                st.markdown("**📦 Reported Listing**")
                st.write("No listing associated")
    
        st.divider()
        st.markdown("**⚡ Admin Actions**")
        
        # Only show resolve button if not already resolved
        if not report.get('resolutionDate'):
            col5, col6, col7 = st.columns(3)
            
            with col5:
                    if st.button("✅ Resolve Report", use_container_width=True, key="resolve_btn"):
                        st.session_state.show_resolve_form = True
            
            with col6:
                if st.button("🚫 Suspend User", use_container_width=True, key="suspend_btn"):
                    st.info("Suspend functionality coming soon")
            
            with col7:
                if st.button("🗑️ Remove Listing", use_container_width=True, key="remove_btn"):
                    st.info("Remove listing functionality coming soon")

                    # Resolve form
            if st.session_state.show_resolve_form:
                st.divider()
                st.subheader("📝 Resolve Report")
                
                with st.form("resolve_form"):
                    resolution_notes = st.text_area(
                        "Resolution Notes",
                        placeholder="Enter details about how this report was resolved...",
                        height=100
                    )
                    
                    col_submit, col_cancel = st.columns(2)
                    
                    with col_submit:
                        submit = st.form_submit_button("✅ Confirm", use_container_width=True)
                    with col_cancel:
                        cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if submit:
                        if not resolution_notes.strip():
                            st.error("Please enter resolution notes")
                        else:
                            try:
                                response = requests.put(
                                    f"{API_URL}/admin/reports/{report.get('reportId')}",
                                    json={"resolution_notes": resolution_notes}
                                )
                                
                                if response.status_code == 200:
                                    st.success("✅ Report resolved successfully!")
                                    st.session_state.show_resolve_form = False
                                    st.session_state.search_result = None
                                    st.rerun()
                                else:
                                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                                    
                            except requests.exceptions.ConnectionError:
                                st.error("Could not connect to API")
                    
                    if cancel:
                        st.session_state.show_resolve_form = False
                        st.rerun()
        else:
            st.success("✅ This report has already been resolved")

# All reports section
st.divider()
st.subheader("📋 All Pending Reports")

# Fetch all reports
try:
    response = requests.get(f"{API_URL}/admin/reports")
    
    if response.status_code == 200:
        reports = response.json()
        
        if len(reports) == 0:
            st.info("No pending reports found.")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            urgent_count = sum(1 for r in reports if r.get("priority") == "URGENT")
            high_count = sum(1 for r in reports if r.get("priority") == "HIGH")
            medium_count = sum(1 for r in reports if r.get("priority") == "MEDIUM")
            
            with col1:
                st.metric("Total Reports", len(reports))
            with col2:
                st.metric("🔴 Urgent", urgent_count)
            with col3:
                st.metric("🟠 High", high_count)
            with col4:
                st.metric("🔵 Medium", medium_count)
            
            st.divider()
            
            # Display each report as a card
            for report in reports:
                priority = report.get("priority", "MEDIUM")
                
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.write(f"**#{report.get('reportId')}**")
                        if priority == "URGENT":
                            st.error(f"🔴 {priority}")
                        elif priority == "HIGH":
                            st.warning(f"🟠 {priority}")
                        else:
                            st.info(f"🔵 {priority}")
                    
                    with col2:
                        st.write(f"**Reason:** {report.get('reason')}")
                    
                    with col3:
                        if st.button("View", key=f"view_{report.get('reportId')}", use_container_width=True):
                            # Fetch full details and show in search result
                            detail_response = requests.get(f"{API_URL}/admin/reports/{report.get('reportId')}")
                            if detail_response.status_code == 200:
                                st.session_state.search_result = detail_response.json()
                                st.rerun()
    else:
        st.error(f"Error fetching reports: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    st.error("Could not connect to API. Make sure Flask is running.")
except Exception as e:
    st.error(f"Error: {e}")