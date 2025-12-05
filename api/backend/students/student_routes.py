from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create Blueprint for student routes
students = Blueprint("students", __name__)


'''
- write an api call that gets all students: and u can input a few different things
like sort by, etc, all in one query
'''


'''
GET /students
Return list of students searchable and filterable
Used by: [Tim-6, Emma-2, Chris-1]
Covers: Search, filter by status, sort by various criteria
'''
@students.route("/", methods=["GET"])
def get_all_students():
    """
    Query params:
    - q: search term (firstName, lastName, email, phone)
    - status: filter by accountStatus (active, suspended, deleted)
    - sortBy: sort by (status, joinDate, lastName)
    - campus: filter by campus
    """
    try:
        current_app.logger.info('GET /students - Getting all students')
        
        # get query parameters
        search_term = request.args.get("q", "")
        status = request.args.get("status", "")
        sort_by = request.args.get("sortBy", "lastName")
        campus = request.args.get("campus", "")
        
        cursor = db.get_db().cursor()
        
        query = """
            SELECT
                stuId,
                CONCAT(firstName, ' ', lastName) AS full_name,
                firstName,
                lastName,
                email,
                phone,
                accountStatus,
                verifiedStatus,
                campus,
                major,
                joinDate
            FROM student
            WHERE 1=1
        """
        
        params = []
        # add search filter if provided (Tim-6, Emma-2)
        if search_term:
            query += """
                AND (firstName LIKE %s
                     OR lastName LIKE %s
                     OR email LIKE %s
                     OR phone LIKE %s
                     OR CONCAT(firstName, ' ', lastName) LIKE %s)
            """
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern] * 5)
        
        # add status filter if provided
        if status:
            query += " AND accountStatus = %s"
            params.append(status)
        
        # add campus filter if provided
        if campus:
            query += " AND campus = %s"
            params.append(campus)
        
        # add sorting
        if sort_by == "status":
            # tim wants suspended first
            query += """
                ORDER BY
                    CASE accountStatus
                        WHEN 'suspended' THEN 1
                        WHEN 'active' THEN 2
                        ELSE 3
                    END,
                    lastName, firstName
            """
        elif sort_by == "joinDate":
            # chris wants newest first
            query += " ORDER BY joinDate DESC"
        else:
            # default alphabetical
            query += " ORDER BY lastName, firstName"
        
        cursor.execute(query, params)
        students_data = cursor.fetchall()  # multiple students
        cursor.close()
        
        current_app.logger.info(f'Successfully retrieved {len(students_data)} students')
        return jsonify(students_data), 200
    except Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({"error": str(e)}), 500


'''
GET /students/{id}
Return detailed student profile
Used by: [Tim-6, Emma-2, Jessica-1]
'''
@students.route("/<int:student_id>", methods=["GET"])
def get_student_profile(student_id):
    try:
        current_app.logger.info(f'GET /students/{student_id} - Getting student profile')
        cursor = db.get_db().cursor()
        
        query = """
            SELECT
                s.stuId,
                s.firstName,
                s.lastName,
                s.email,
                s.phone,
                s.major,
                s.bio,
                s.verifiedStatus,
                s.accountStatus,
                s.campus,
                s.profilePhotoUrl,
                s.joinDate,
                COUNT(DISTINCT l.listingId) AS total_services,
                AVG(r.rating) AS avg_rating,
                COUNT(DISTINCT r.reviewId) AS total_reviews
            FROM student s
            LEFT JOIN listing l ON s.stuId = l.providerId
            LEFT JOIN review r ON l.listingId = r.listId
            WHERE s.stuId = %s
            GROUP BY s.stuId, s.firstName, s.lastName, s.email, s.phone,
                     s.major, s.bio, s.verifiedStatus, s.accountStatus,
                     s.campus, s.profilePhotoUrl, s.joinDate
        """
        
        cursor.execute(query, (student_id,))
        profile = cursor.fetchone()  # 1 student
        cursor.close()
        
        if not profile:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify(profile), 200
    except Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({"error": str(e)}), 500




'''
# ============================================
# USER STORY 1.2: Get student profile with ratings
# As a student seeking help, I want to see verified student profiles with ratings
# ============================================
@students.route("/students/<int:student_id>", methods=["GET"])
def get_student_profile(student_id):
    try:
        current_app.logger.info(f'Getting profile for student {student_id}')
        cursor = db.get_db().cursor()
        
        query = """
            SELECT
                s.stuId,
                s.firstName,
                s.lastName,
                s.email,
                s.phone,
                s.major,
                s.bio,
                s.verifiedStatus,
                s.profilePhotoUrl,
                COUNT(DISTINCT l.listingId) AS total_services,
                AVG(r.rating) AS avg_rating,
                COUNT(DISTINCT r.reviewId) AS total_reviews
            FROM student s
            LEFT JOIN listing l ON s.stuId = l.providerId
            LEFT JOIN review r ON l.listingId = r.listId
            WHERE s.stuId = %s AND s.verifiedStatus = TRUE
            GROUP BY s.stuId, s.firstName, s.lastName, s.email, s.phone,
                     s.major, s.bio, s.verifiedStatus, s.profilePhotoUrl
        """
        
        cursor.execute(query, (student_id,))
        profile = cursor.fetchone()
        cursor.close()
        
        if not profile:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify(profile), 200
    except Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 2.1: Update student profile
# As a service provider, I want to create a comprehensive profile
# ============================================
@students.route("/students/<int:student_id>", methods=["PUT"])
def update_student_profile(student_id):
    try:
        data = request.get_json()
        cursor = db.get_db().cursor()
        
        query = """
            UPDATE student
            SET bio = %s,
                major = %s,
                phone = %s,
                profilePhotoUrl = %s
            WHERE stuId = %s
        """
        
        cursor.execute(query, (
            data.get('bio'),
            data.get('major'),
            data.get('phone'),
            data.get('profilePhotoUrl'),
            student_id
        ))
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Profile updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 3.2: Verify student account
# As an admin, I want to verify student accounts
# ============================================
@students.route("/students/<int:student_id>/verify", methods=["PUT"])
def verify_student(student_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
            UPDATE student
            SET verifiedStatus = TRUE,
                accountStatus = 'active'
            WHERE email LIKE '%@northeastern.edu'
              AND stuId = %s
              AND verifiedStatus = FALSE
        """
        
        cursor.execute(query, (student_id,))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found or already verified"}), 404
            
        cursor.close()
        return jsonify({"message": "Student verified successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 3.6: Search for users
# As an admin, I want to search for specific users by name, email
# ============================================
@students.route("/students/search", methods=["GET"])
def search_students():
    try:
        search_term = request.args.get("q", "")
        
        cursor = db.get_db().cursor()
        query = """
            SELECT
                stuId,
                CONCAT(firstName, ' ', lastName) AS full_name,
                email,
                phone,
                accountStatus,
                verifiedStatus,
                campus,
                major,
                joinDate
            FROM student
            WHERE
                firstName LIKE %s
                OR lastName LIKE %s
                OR email LIKE %s
                OR phone LIKE %s
                OR CONCAT(firstName, ' ', lastName) LIKE %s
            ORDER BY lastName, firstName
        """
        
        search_pattern = f"%{search_term}%"
        cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 3.4: See user ratings and service history
# As an admin, I want to see user ratings and service history at a glance
# ============================================
@students.route("/students/<int:student_id>/ratings", methods=["GET"])
def get_student_ratings(student_id):
    try:
        cursor = db.get_db().cursor()
        
        # Average rating query
        query = """
            SELECT provider.stuID AS providerId,
                   CONCAT(provider.firstName, ' ', provider.lastName) AS provider_name,
                   AVG(r.rating) AS avg_rating,
                   provider.accountStatus
            FROM student provider
            JOIN listing l ON provider.stuId = l.providerId
            JOIN review r ON l.listingId = r.listId
            WHERE provider.stuId = %s
            GROUP BY provider.stuId, provider.accountStatus
        """
        
        cursor.execute(query, (student_id,))
        rating = cursor.fetchone()
        cursor.close()
        
        if not rating:
            return jsonify({"error": "No ratings found for this student"}), 404
            
        return jsonify(rating), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 3.5: Suspend student account
# As an admin, I want to suspend accounts
# ============================================
@students.route("/students/<int:student_id>/suspend", methods=["PUT"])
def suspend_student(student_id):
    try:
        cursor = db.get_db().cursor()
        
        # Update student account status
        query = """
            UPDATE student
            SET accountStatus = 'suspended'
            WHERE stuId = %s
        """
        
        cursor.execute(query, (student_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Student suspended successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 4.4: Sort users by registration date (PM analytics)
# As a PM, I want to filter and sort users by registration date
# ============================================
@students.route("/students/by-registration", methods=["GET"])
def get_students_by_registration():
    try:
        cursor = db.get_db().cursor()
        
        query = """
            SELECT *
            FROM student
            ORDER BY student.joinDate DESC
        """
        
        cursor.execute(query)
        students_data = cursor.fetchall()
        cursor.close()
        
        return jsonify(students_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 4.4: Sort users by average rating (PM analytics)
# ============================================
@students.route("/students/by-rating", methods=["GET"])
def get_students_by_rating():
    try:
        cursor = db.get_db().cursor()
        
        query = """
            SELECT s.*, provider.avg_rating
            FROM(
                SELECT s.stuId, AVG(r.rating) AS avg_rating
                FROM student s JOIN listing l ON l.providerId = s.stuId
                               JOIN review r ON r.listId = l.listingId
                GROUP BY s.stuId
            ) AS provider JOIN student AS s ON s.stuid = provider.stuId
            ORDER BY provider.avg_rating DESC
        """
        
        cursor.execute(query)
        students_data = cursor.fetchall()
        cursor.close()
        
        return jsonify(students_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# USER STORY 4.4: Sort users by transaction count (PM analytics)
# ============================================
@students.route("/students/by-transaction-count", methods=["GET"])
def get_students_by_transaction_count():
    try:
        cursor = db.get_db().cursor()
        
        query = """
            SELECT s.*, st.count
            FROM (
                SELECT buyerId AS stuId, COUNT(*) AS count
                FROM transact
                GROUP BY buyerId
            ) AS st
            JOIN student s ON s.stuId = st.stuId
            ORDER BY st.count DESC
        """
        
        cursor.execute(query)
        students_data = cursor.fetchall()
        cursor.close()
        
        return jsonify(students_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500



# ============================================
# GET /students/{id}
# Return detailed student profile
# Used by: [Tim-6, Emma-2, Jessica-1]
# ============================================
@students.route("/students/<int:student_id>", methods=["GET"])
def get_student_profile(student_id):
    try:
        current_app.logger.info(f'udhcuhcuet {student_id}')
        cursor = db.get_db().cursor()
        
        query = """
            query cejnckewmcoqemo
        """
        
        cursor.execute(query, (student_id,))
        profile = cursor.fetchone() # we use fetchone instead??? and then /GET students would be all?
        cursor.close()
        
        if not profile:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify(profile), 200
    except Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({"error": str(e)}), 500



all places u use endpoint, put all data together and then streamlit doe sthe filter
OR 
have a version of the endpoint so 

write one get reqiest that gets all detailed info and then in streamlit basically filter out 
for this partocular i need a name and a date or etc. $/hour, etc
'''
