import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("👥 User Management")

# API URL
API_URL = "http://web-api:4000"

# Initialize session state
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "View All Users"
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None
if "search_user_id_value" not in st.session_state:
    st.session_state.search_user_id_value = 1
if "show_suspend_form" not in st.session_state:
    st.session_state.show_suspend_form = False

# Check if coming from Reports page
if "search_user_id" in st.session_state and st.session_state.search_user_id is not None:
    user_id = st.session_state.search_user_id
    st.session_state.search_user_id = None
    st.session_state.search_user_id_value = user_id
    st.session_state.active_tab = "Search Users"
    st.session_state.show_suspend_form = False
    
    # Fetch user details
    try:
        response = requests.get(f"{API_URL}/students/{user_id}")
        if response.status_code == 200:
            st.session_state.selected_user = response.json()
    except Exception as e:
        st.error(f"Could not fetch user details: {e}")

# Tabs - order changes based on active_tab
if st.session_state.active_tab == "Search Users":
    tab2, tab1, tab3 = st.tabs(["Search Users", "View All Users", "Suspensions"])
else:
    tab1, tab2, tab3 = st.tabs(["View All Users", "Search Users", "Suspensions"])


# ============================================================
# SEARCH USERS TAB
# ============================================================
with tab2:
    st.subheader("🔍 Search Users")
    
    # Search bar
    col1, col2 = st.columns([3, 1])
    with col1:
        search_id = st.number_input(
            "Enter Student ID", 
            min_value=1, 
            step=1, 
            value=st.session_state.search_user_id_value,
            key="search_user_id_input",
            label_visibility="collapsed"
        )
    with col2:
        search_clicked = st.button("🔍 Search", key="search_user_btn", use_container_width=True)
    
    if search_clicked:
        try:
            response = requests.get(f"{API_URL}/students/{search_id}")
            if response.status_code == 200:
                st.session_state.selected_user = response.json()
                st.session_state.search_user_id_value = search_id
                st.session_state.show_suspend_form = False
                st.rerun()
            else:
                st.warning(f"User #{search_id} not found")
                st.session_state.selected_user = None
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to API: {e}")
    
    # Clear button
    if st.session_state.selected_user is not None:
        if st.button("✖ Clear/Back", key="clear_user_search"):
            st.session_state.selected_user = None
            st.session_state.show_suspend_form = False
            st.session_state.active_tab = "View All Users"
            st.rerun()
    
    # Display selected user details
    if st.session_state.selected_user is not None:
        st.divider()
        
        user = st.session_state.selected_user
        
        st.subheader(f"👤 {user.get('firstName')} {user.get('lastName')}")
        
        # Status badge
        status = user.get('accountStatus', 'active')
        if status == 'suspended':
            st.error("🚫 Account Status: Suspended")
        else:
            st.success("✅ Account Status: Active")
        
        # User info columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📋 Basic Info**")
            st.write(f"**ID:** {user.get('stuId')}")
            st.write(f"**Email:** {user.get('email')}")
            st.write(f"**Phone:** {user.get('phone') or 'N/A'}")
            st.write(f"**Major:** {user.get('major') or 'N/A'}")
            st.write(f"**Campus:** {user.get('campus') or 'N/A'}")
        with col2:
            st.markdown("**📊 Stats**")
            st.write(f"**Verified:** {'✅' if user.get('verifiedStatus') else '❌'}")
            st.write(f"**Services:** {user.get('total_services', 0)}")
            avg_rating = user.get('avg_rating') or 0
            st.write(f"**Rating:** ⭐ {avg_rating}")
            st.write(f"**Reviews:** {user.get('total_reviews', 0)}")
            join_date = user.get('joinDate', 'N/A')
            if join_date and join_date != 'N/A':
                st.write(f"**Joined:** {str(join_date)[:10]}")
            else:
                st.write(f"**Joined:** N/A")
        
        # Bio section
        if user.get('bio'):
            st.divider()
            st.markdown("**📝 Bio**")
            st.write(user.get('bio'))
        
        # Action buttons
        st.divider()
        st.markdown("**⚡ Admin Actions**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if status != 'suspended':
                if st.button("🚫 Suspend User", use_container_width=True, key="suspend_user_btn"):
                    st.session_state.show_suspend_form = True
                    st.rerun()
            else:
                if st.button("✅ Unsuspend User", use_container_width=True, key="unsuspend_user_btn"):
                    try:
                        resp = requests.put(f"{API_URL}/students/{user.get('stuId')}/unsuspend")
                        if resp.status_code == 200:
                            st.success("User unsuspended!")
                            st.session_state.selected_user = None
                            st.session_state.show_suspend_form = False
                            st.rerun()
                        else:
                            st.error("Failed to unsuspend user")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
        
        with col2:
            if not user.get('verifiedStatus'):
                if st.button("🔍 Verify User", use_container_width=True, key="verify_user_btn"):
                    try:
                        resp = requests.put(f"{API_URL}/students/{user.get('stuId')}/verify")
                        if resp.status_code == 200:
                            st.success("User verified!")
                            st.session_state.selected_user = None
                            st.rerun()
                        else:
                            st.error("Failed to verify user")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
        
        # Suspend Form - shows when button is clicked
        if st.session_state.show_suspend_form and status != 'suspended':
            st.divider()
            st.subheader("🚫 Create Suspension")
            
            with st.form("suspend_form"):
                suspension_type = st.selectbox("Suspension Type", ["temp", "perm"])
                
                if suspension_type == "temp":
                    end_date = st.date_input(
                        "End Date",
                        value=datetime.now() + timedelta(days=7),
                        min_value=datetime.now()
                    )
                else:
                    end_date = None
                    st.info("Permanent suspensions have no end date")
                
                reason = st.text_area(
                    "Reason for Suspension",
                    placeholder="Enter the reason for this suspension...",
                    height=100
                )
                
                col_submit, col_cancel = st.columns(2)
                
                with col_submit:
                    submit = st.form_submit_button("✅ Confirm Suspension", use_container_width=True)
                with col_cancel:
                    cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if submit:
                    try:
                        payload = {
                            "stuId": user.get('stuId'),
                            "type": suspension_type,
                            "endDate": end_date.strftime("%Y-%m-%d") if end_date else None
                        }
                        
                        resp = requests.post(f"{API_URL}/admin/suspensions", json=payload)
                        
                        if resp.status_code == 201:
                            st.success("✅ User suspended successfully!")
                            st.session_state.show_suspend_form = False
                            st.session_state.selected_user = None
                            st.rerun()
                        else:
                            error_msg = resp.json().get('error', 'Unknown error')
                            st.error(f"Error: {error_msg}")
                    except requests.exceptions.RequestException:
                        st.error("Could not connect to API")
                
                if cancel:
                    st.session_state.show_suspend_form = False
                    st.rerun()


# ============================================================
# VIEW ALL USERS TAB
# ============================================================
with tab1:
    st.subheader("View All Users")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("Sort by", ["joinDate", "lastName", "status"], key="sort_select")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["", "active", "suspended"], key="status_filter")
    with col3:
        search_term = st.text_input("Search", placeholder="Name, email, phone...", key="search_input")
    
    try:
        # Build query params
        params = {"sortBy": sort_by}
        if status_filter:
            params["status"] = status_filter
        if search_term:
            params["q"] = search_term
        
        response = requests.get(f"{API_URL}/students", params=params)
        
        if response.status_code == 200:
            students = response.json()
            
            if len(students) == 0:
                st.info("No users found.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Users", len(students))
                with col2:
                    active_count = sum(1 for s in students if s.get("accountStatus") == "active")
                    st.metric("✅ Active", active_count)
                with col3:
                    suspended_count = sum(1 for s in students if s.get("accountStatus") == "suspended")
                    st.metric("🚫 Suspended", suspended_count)
                
                st.divider()
                
                # Display user cards
                for student in students:
                    stu_id = student.get("stuId")
                    first_name = student.get("firstName", "")
                    last_name = student.get("lastName", "")
                    full_name = student.get("full_name", f"{first_name} {last_name}")
                    email = student.get("email", "N/A")
                    status = student.get("accountStatus", "active")
                    verified = student.get("verifiedStatus", False)
                    
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            st.write(f"**#{stu_id}**")
                            if status == "suspended":
                                st.error("🚫 Suspended")
                            else:
                                st.success("✅ Active")
                        
                        with col2:
                            st.write(f"**Name:** {full_name}")
                            st.write(f"**Email:** {email}")
                            st.write(f"**Verified:** {'✅' if verified else '❌'}")
                        
                        with col3:
                            if st.button("View", key=f"view_user_{stu_id}", use_container_width=True):
                                # Store user ID and switch to Search tab
                                st.session_state.search_user_id_value = stu_id
                                st.session_state.active_tab = "Search Users"
                                st.session_state.show_suspend_form = False
                                
                                # Fetch user details
                                fetch_success = False
                                try:
                                    resp = requests.get(f"{API_URL}/students/{stu_id}")
                                    if resp.status_code == 200:
                                        st.session_state.selected_user = resp.json()
                                        fetch_success = True
                                    else:
                                        st.error(f"User not found: {resp.status_code}")
                                except requests.exceptions.RequestException as e:
                                    st.error(f"Could not fetch user: {e}")
                                
                                if fetch_success:
                                    st.rerun()
        else:
            st.error(f"Error: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to API: {e}")


# ============================================================
# SUSPENSIONS TAB
# ============================================================
with tab3:
    st.subheader("🚫 Suspensions")
    
    try:
        response = requests.get(f"{API_URL}/admin/suspensions")
        
        if response.status_code == 200:
            suspensions = response.json()
            
            if len(suspensions) == 0:
                st.info("No suspensions found.")
            else:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                active_count = sum(1 for s in suspensions if s.get("status") == "ACTIVE")
                permanent_count = sum(1 for s in suspensions if s.get("status") == "PERMANENT")
                expired_count = sum(1 for s in suspensions if s.get("status") == "EXPIRED")
                
                with col1:
                    st.metric("Total", len(suspensions))
                with col2:
                    st.metric("🟠 Active", active_count)
                with col3:
                    st.metric("🔴 Permanent", permanent_count)
                with col4:
                    st.metric("🔵 Expired", expired_count)
                
                st.divider()
                
                # Filter options
                filter_status = st.selectbox(
                    "Filter by Status",
                    ["All", "ACTIVE", "PERMANENT", "EXPIRED"],
                    key="suspension_filter_status"
                )
                
                # Filter suspensions
                filtered_suspensions = suspensions
                if filter_status != "All":
                    filtered_suspensions = [s for s in suspensions if s.get("status") == filter_status]
                
                # Display suspension cards
                for suspension in filtered_suspensions:
                    suspension_status = suspension.get("status", "ACTIVE")
                    
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**#{suspension.get('suspensionId')}**")
                            if suspension_status == "PERMANENT":
                                st.error(f"🔴 {suspension_status}")
                            elif suspension_status == "ACTIVE":
                                st.warning(f"🟠 {suspension_status}")
                            else:
                                st.info(f"🔵 {suspension_status}")
                        
                        with col2:
                            st.write(f"**Student:** {suspension.get('firstName')} {suspension.get('lastName')}")
                            st.write(f"**Email:** {suspension.get('email')}")
                            st.write(f"**Student ID:** {suspension.get('stuId')}")
                        
                        with col3:
                            st.write(f"**Type:** {suspension.get('type')}")
                            start_date = suspension.get('startDate')
                            if start_date:
                                st.write(f"**Start:** {str(start_date)[:10]}")
                            end_date = suspension.get('endDate')
                            if end_date:
                                st.write(f"**End:** {str(end_date)[:10]}")
                            else:
                                st.write("**End:** Never (Permanent)")
                            if suspension.get('report_reason'):
                                st.write(f"**Reason:** {suspension.get('report_reason')}")
                        
                        with col4:
                            # Lift suspension button (only for active/permanent)
                            if suspension_status in ["ACTIVE", "PERMANENT"]:
                                if st.button("Lift", key=f"lift_{suspension.get('suspensionId')}", use_container_width=True):
                                    try:
                                        resp = requests.delete(f"{API_URL}/admin/suspensions/{suspension.get('suspensionId')}")
                                        if resp.status_code == 200:
                                            st.success("Suspension lifted!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to lift suspension")
                                    except:
                                        st.error("Could not connect to API")
        else:
            st.error(f"Error fetching suspensions: {response.status_code}")
    except requests.exceptions.RequestException:
        st.error("Could not connect to API")