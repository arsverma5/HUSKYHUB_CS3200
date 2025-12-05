import streamlit as st
import requests
from datetime import datetime, timedelta
from modules.nav import SideBarLinks

SideBarLinks(show_home=True)

st.title("👥 User Management")

# API URL
API_URL = "http://web-api:4000"

# Initialize session state
if "selected_suspension" not in st.session_state:
    st.session_state.selected_suspension = None
if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False
if "show_edit_form" not in st.session_state:
    st.session_state.show_edit_form = False
if "selected_user" not in st.session_state:
    st.session_state.selected_user = None

# ============== TABS ==============
tab1, tab2 = st.tabs(["🚫 Suspensions", "👤 All Users"])

# ============== SUSPENSIONS TAB ==============
with tab1:
    st.subheader("🚫 Suspension Management")
    
    # Create new suspension button
    if st.button("➕ Create New Suspension", key="create_suspension_btn"):
        st.session_state.show_create_form = True
        st.session_state.selected_suspension = None
        st.session_state.show_edit_form = False
    
    # ============== CREATE SUSPENSION FORM ==============
    if st.session_state.show_create_form:
        st.divider()
        st.subheader("📝 Create New Suspension")
        
        with st.form("create_suspension_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                stu_id = st.number_input("Student ID", min_value=1, step=1)
                suspension_type = st.selectbox("Suspension Type", ["temporary", "permanent"])
            
            with col2:
                report_id = st.number_input("Report ID (optional)", min_value=0, step=1, help="Enter 0 if no report")
                
                if suspension_type == "temporary":
                    end_date = st.date_input(
                        "End Date",
                        value=datetime.now() + timedelta(days=7),
                        min_value=datetime.now()
                    )
                else:
                    end_date = None
                    st.info("Permanent suspensions have no end date")
            
            col_submit, col_cancel = st.columns(2)
            
            with col_submit:
                submit = st.form_submit_button("✅ Create Suspension", use_container_width=True)
            with col_cancel:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit:
                try:
                    payload = {
                        "stuId": stu_id,
                        "type": suspension_type,
                        "reportId": report_id if report_id > 0 else None,
                        "endDate": end_date.strftime("%Y-%m-%d") if end_date else None
                    }
                    
                    response = requests.post(f"{API_URL}/admin/suspensions", json=payload)
                    
                    if response.status_code == 201:
                        st.success("✅ Suspension created successfully!")
                        st.session_state.show_create_form = False
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to API")
                except Exception as e:
                    st.error(f"Error: {e}")
            
            if cancel:
                st.session_state.show_create_form = False
                st.rerun()
    
    # ============== SELECTED SUSPENSION DETAILS ==============
    if st.session_state.selected_suspension is not None:
        st.divider()
        
        suspension = st.session_state.selected_suspension
        
        st.subheader(f"📋 Suspension #{suspension.get('suspensionId')} Details")
        
        # Status badge
        status = suspension.get("status", "ACTIVE")
        if status == "PERMANENT":
            st.error(f"🔴 Status: {status}")
        elif status == "ACTIVE":
            st.warning(f"🟠 Status: {status}")
        else:
            st.info(f"🔵 Status: {status}")
        
        # Details in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**👤 Student Information**")
            st.write(f"**Name:** {suspension.get('firstName')} {suspension.get('lastName')}")
            st.write(f"**Email:** {suspension.get('email')}")
            st.write(f"**Student ID:** {suspension.get('stuId')}")
            st.write(f"**Account Status:** {suspension.get('accountStatus')}")
        
        with col2:
            st.markdown("**🚫 Suspension Details**")
            st.write(f"**Type:** {suspension.get('type')}")
            st.write(f"**Start Date:** {suspension.get('startDate')}")
            st.write(f"**End Date:** {suspension.get('endDate') or 'Never (Permanent)'}")
            if suspension.get('days_remaining'):
                st.write(f"**Days Remaining:** {suspension.get('days_remaining')}")
        
        # Report info if available
        if suspension.get('reportId'):
            st.divider()
            st.markdown("**📄 Related Report**")
            st.write(f"**Report ID:** {suspension.get('reportId')}")
            st.write(f"**Reason:** {suspension.get('report_reason')}")
            if suspension.get('reportDetails'):
                st.write(f"**Details:** {suspension.get('reportDetails')}")
        
        st.divider()
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✏️ Edit Suspension", use_container_width=True, key="edit_suspension_btn"):
                st.session_state.show_edit_form = True
        
        with col2:
            if st.button("🔓 Lift Suspension", use_container_width=True, key="lift_suspension_btn"):
                try:
                    response = requests.delete(f"{API_URL}/admin/suspensions/{suspension.get('suspensionId')}")
                    
                    if response.status_code == 200:
                        st.success("✅ Suspension lifted successfully!")
                        st.session_state.selected_suspension = None
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to API")
        
        with col3:
            if st.button("✖ Close", use_container_width=True, key="close_details_btn"):
                st.session_state.selected_suspension = None
                st.session_state.show_edit_form = False
                st.rerun()
        
        # ============== EDIT FORM ==============
        if st.session_state.show_edit_form:
            st.divider()
            st.subheader("✏️ Edit Suspension")
            
            with st.form("edit_suspension_form"):
                new_type = st.selectbox(
                    "Suspension Type",
                    ["temporary", "permanent"],
                    index=0 if suspension.get('type') == 'temporary' else 1
                )
                
                if new_type == "temporary":
                    current_end = None
                    if suspension.get('endDate'):
                        try:
                            current_end = datetime.strptime(suspension.get('endDate')[:10], "%Y-%m-%d")
                        except:
                            current_end = datetime.now() + timedelta(days=7)
                    else:
                        current_end = datetime.now() + timedelta(days=7)
                    
                    new_end_date = st.date_input(
                        "New End Date",
                        value=current_end,
                        min_value=datetime.now()
                    )
                else:
                    new_end_date = None
                    st.info("Permanent suspensions have no end date")
                
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    save = st.form_submit_button("💾 Save Changes", use_container_width=True)
                with col_cancel:
                    cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if save:
                    try:
                        payload = {"type": new_type}
                        
                        if new_type == "temporary" and new_end_date:
                            payload["endDate"] = new_end_date.strftime("%Y-%m-%d")
                        
                        response = requests.put(
                            f"{API_URL}/admin/suspensions/{suspension.get('suspensionId')}",
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ Suspension updated successfully!")
                            st.session_state.show_edit_form = False
                            st.session_state.selected_suspension = None
                            st.rerun()
                        else:
                            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                            
                    except requests.exceptions.ConnectionError:
                        st.error("Could not connect to API")
                
                if cancel_edit:
                    st.session_state.show_edit_form = False
                    st.rerun()

# ============== ALL USERS TAB ==============
with tab2:
    st.subheader("👤 All Users")
    
    # Search box
    search_query = st.text_input("🔍 Search users by name, email, or phone", key="user_search")
    
    # Sort options
    sort_option = st.selectbox(
        "Sort by",
        ["Registration Date", "Rating", "Transaction Count"],
        key="sort_option"
    )
    
    try:
        # Use different endpoints based on sort option (DOUBLED /students/students/)
        if search_query:
            response = requests.get(f"{API_URL}/students/students/search", params={"q": search_query})
        elif sort_option == "Registration Date":
            response = requests.get(f"{API_URL}/students/students/by-registration")
        elif sort_option == "Rating":
            response = requests.get(f"{API_URL}/students/students/by-rating")
        else:  # Transaction Count
            response = requests.get(f"{API_URL}/students/students/by-transaction-count")
        
        if response.status_code == 200:
            students = response.json()
            
            if len(students) == 0:
                st.info("No users found.")
            else:
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                
                active_count = sum(1 for s in students if s.get("accountStatus") == "active")
                suspended_count = sum(1 for s in students if s.get("accountStatus") == "suspended")
                verified_count = sum(1 for s in students if s.get("verifiedStatus"))
                
                with col1:
                    st.metric("Total Users", len(students))
                with col2:
                    st.metric("✅ Active", active_count)
                with col3:
                    st.metric("🚫 Suspended", suspended_count)
                
                st.divider()
                
                # Filter by account status
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Active", "Suspended"],
                    key="user_status_filter"
                )
                
                # Apply filter
                if status_filter == "Active":
                    students = [s for s in students if s.get("accountStatus") == "active"]
                elif status_filter == "Suspended":
                    students = [s for s in students if s.get("accountStatus") == "suspended"]
                
                # Display users
                for student in students:
                    stu_id = student.get("stuId")
                    first_name = student.get("firstName", "")
                    last_name = student.get("lastName", "")
                    full_name = student.get("full_name", f"{first_name} {last_name}")
                    email = student.get("email", "N/A")
                    status = student.get("accountStatus", "active")
                    verified = student.get("verifiedStatus", False)
                    major = student.get("major", "")
                    avg_rating = student.get("avg_rating")
                    transaction_count = student.get("count")
                    join_date = student.get("joinDate")
                    
                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                        
                        with col1:
                            st.write(f"**#{stu_id}**")
                            if status == "suspended":
                                st.error("🚫 Suspended")
                            else:
                                st.success("✅ Active")
                        
                        with col2:
                            st.write(f"**Name:** {full_name}")
                            st.write(f"**Email:** {email}")
                        
                        with col3:
                            st.write(f"**Verified:** {'✅' if verified else '❌'}")
                            if major:
                                st.write(f"**Major:** {major}")
                            if avg_rating:
                                st.write(f"**Rating:** ⭐ {round(avg_rating, 2)}")
                            if transaction_count:
                                st.write(f"**Transactions:** {transaction_count}")
                            if join_date:
                                st.write(f"**Joined:** {str(join_date)[:10]}")
                        
                        with col4:
                            # View details button
                            if st.button("View", key=f"view_user_{stu_id}", use_container_width=True):
                                try:
                                    detail_response = requests.get(f"{API_URL}/students/students/{stu_id}")
                                    if detail_response.status_code == 200:
                                        st.session_state.selected_user = detail_response.json()
                                        st.rerun()
                                except:
                                    st.error("Could not fetch user details")
                            
                            # Suspend button (only show if NOT suspended)
                            if status != "suspended":
                                if st.button("🚫 Suspend", key=f"suspend_user_{stu_id}", use_container_width=True, type="secondary"):
                                    try:
                                        suspend_response = requests.put(f"{API_URL}/students/students/{stu_id}/suspend")
                                        if suspend_response.status_code == 200:
                                            st.success("User suspended!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to suspend user")
                                    except:
                                        st.error("Could not connect to API")
                            
                            # Unsuspend button (only show if suspended)
                            if status == "suspended":
                                if st.button("✅ Unsuspend", key=f"unsuspend_user_{stu_id}", use_container_width=True, type="primary"):
                                    try:
                                        unsuspend_response = requests.put(f"{API_URL}/students/students/{stu_id}/unsuspend")
                                        if unsuspend_response.status_code == 200:
                                            st.success("User unsuspended!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to unsuspend user")
                                    except:
                                        st.error("Could not connect to API")
                            
                            # Verify button (only show if NOT verified)
                            if not verified:
                                if st.button("🔍 Verify", key=f"verify_user_{stu_id}", use_container_width=True, type="secondary"):
                                    try:
                                        verify_response = requests.put(f"{API_URL}/students/students/{stu_id}/verify")
                                        if verify_response.status_code == 200:
                                            st.success("User verified!")
                                            st.rerun()
                                        else:
                                            st.error("Failed to verify user")
                                    except:
                                        st.error("Could not connect to API")
        else:
            st.error(f"Error fetching users: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        st.error("❌ Could not connect to API. Make sure Flask is running.")
    except Exception as e:
        st.error(f"Error: {e}")
    
    # ============== SELECTED USER DETAILS ==============
    if st.session_state.selected_user is not None:
        st.divider()
        user = st.session_state.selected_user
        
        st.subheader(f"👤 User Details: {user.get('firstName')} {user.get('lastName')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📋 Basic Information**")
            st.write(f"**Student ID:** {user.get('stuId')}")
            st.write(f"**Name:** {user.get('firstName')} {user.get('lastName')}")
            st.write(f"**Email:** {user.get('email')}")
            st.write(f"**Phone:** {user.get('phone') or 'N/A'}")
            st.write(f"**Major:** {user.get('major') or 'N/A'}")
        
        with col2:
            st.markdown("**📊 Stats**")
            st.write(f"**Verified:** {'✅ Yes' if user.get('verifiedStatus') else '❌ No'}")
            st.write(f"**Total Services:** {user.get('total_services', 0)}")
            st.write(f"**Average Rating:** ⭐ {round(user.get('avg_rating', 0) or 0, 2)}")
            st.write(f"**Total Reviews:** {user.get('total_reviews', 0)}")
        
        if user.get('bio'):
            st.divider()
            st.markdown("**📝 Bio**")
            st.write(user.get('bio'))
        
        # Fetch user ratings (DOUBLED path)
        try:
            ratings_response = requests.get(f"{API_URL}/students/students/{user.get('stuId')}/ratings")
            if ratings_response.status_code == 200:
                ratings = ratings_response.json()
                st.divider()
                st.markdown("**⭐ Rating Details**")
                st.write(f"**Provider Name:** {ratings.get('provider_name')}")
                st.write(f"**Average Rating:** {round(ratings.get('avg_rating', 0), 2)}")
        except:
            pass
        
        # Fetch user metrics (DOUBLED path)
        try:
            metrics_response = requests.get(f"{API_URL}/students/students/{user.get('stuId')}/metrics")
            if metrics_response.status_code == 200:
                metrics = metrics_response.json()
                st.divider()
                st.markdown("**📈 Provider Metrics**")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Active Services", metrics.get('active_services', 0))
                with col2:
                    st.metric("Total Bookings", metrics.get('total_bookings', 0))
                with col3:
                    st.metric("Completed", metrics.get('completed_bookings', 0))
                with col4:
                    st.metric("Total Earnings", f"${metrics.get('total_earnings', 0):.2f}")
        except:
            pass
        
        # Close button
        if st.button("✖ Close Details", key="close_user_details"):
            st.session_state.selected_user = None
            st.rerun()