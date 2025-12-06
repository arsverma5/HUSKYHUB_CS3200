import streamlit as st
import requests
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("Reports Dashboard")

# API URL
API_URL = "http://web-api:4000"

# Initialize session states
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "show_resolve_form" not in st.session_state:
    st.session_state.show_resolve_form = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "View All Reports"    

# Tabs
if st.session_state.active_tab == "Search Reports":
    tab2, tab1 = st.tabs(["Search Reports", "View All Reports"])
else:
    tab1, tab2 = st.tabs(["View All Reports", "Search Reports"])

# Search tab
with tab2:
    st.subheader("🔍 Search Report by ID")
    col1, col2 = st.columns([3, 1])
    with col1:
        report_id = st.number_input("Enter Report ID", min_value=1, step=1, value=1, label_visibility="collapsed")
    with col2:
        search_clicked = st.button("🔍 Search", use_container_width=True, key="search_btn")
    
    if search_clicked:
        try:
            response = requests.get(f"{API_URL}/admin/reports/{report_id}")
            
            if response.status_code == 200:
                st.session_state.search_result = response.json()
                st.session_state.show_resolve_form = False
                st.rerun()
            elif response.status_code == 404:
                st.warning(f"⚠️ Report #{report_id} not found")
            else:
                st.error("❌ An error occurred")
                
        except requests.exceptions.ConnectionError:
            st.error("❌ Could not connect to API.")

    # Clear search button
    if st.session_state.search_result is not None and st.session_state.search_result not in ["not_found", "connection_error", "error"]:
        if st.button("✖ Clear/Back", key="clear_search_btn"):
            st.session_state.search_result = None
            st.session_state.active_tab = "View All Reports"
            st.rerun()

    # Display search results
    if st.session_state.search_result is not None and st.session_state.search_result not in ["not_found", "connection_error", "error"]:
        st.divider()
        
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
            st.write(f"**ID:** {report.get('reported_student_id')}")
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
        
        # Only show buttons if not already resolved
        if not report.get('resolutionDate'):
            col5, col6, col7 = st.columns(3)
            
            with col5:
                if st.button("✅ Resolve Report", use_container_width=True, key="resolve_btn"):
                    st.session_state.show_resolve_form = True
                    st.rerun()
            
            with col6:
                # Get the reported student ID
                reported_id = report.get('reported_student_id')
                if reported_id:
                    if st.button("👤 View Reported User", use_container_width=True, key="view_user_btn"):
                        st.session_state.search_user_id = reported_id
                        st.switch_page("pages/32_User_Management.py")
                else:
                    st.button("👤 View Reported User", use_container_width=True, disabled=True, key="view_user_btn_disabled")
                    st.caption("No user ID available")
            
            with col7:
                # Get the reported listing id
                reported_list_id = report.get('listing_id')
                if reported_list_id:
                    if st.button("📦 View Listing", use_container_width=True, key="view_listing_btn"):
                        st.session_state.search_listing_id = reported_list_id
                        st.switch_page("pages/33_Listing_Management.py")
                else:
                    st.button("📦 View Listing", use_container_width=True, disabled=True, key="view_listing_btn_disabled")
                    st.caption("No Listing ID available")

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
                                    st.session_state.active_tab = "View All Reports"
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

# All reports tab
with tab1:
    st.subheader("Report Summary")

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
                st.subheader("View All Reports")

                # Display each report as a card
                for report in reports:
                    priority = report.get("priority", "MEDIUM")
                    report_id = report.get('reportId')
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            st.write(f"**#{report_id}**")
                            if priority == "URGENT":
                                st.error(f"🔴 {priority}")
                            elif priority == "HIGH":
                                st.warning(f"🟠 {priority}")
                            else:
                                st.info(f"🔵 {priority}")
                        
                        with col2:
                            st.write(f"**Reason:** {report.get('reason')}")
                        
                        with col3:
                            if st.button("View", key=f"view_{report_id}", use_container_width=True):
                                detail_response = requests.get(f"{API_URL}/admin/reports/{report_id}")
                                if detail_response.status_code == 200:
                                    st.session_state.search_result = detail_response.json()
                                    st.session_state.active_tab = "Search Reports"
                                    st.session_state.show_resolve_form = False
                                    st.rerun()
        else:
            st.error(f"Error fetching reports: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to API. Make sure Flask is running.")
    except Exception as e:
        st.error(f"Error: {e}")