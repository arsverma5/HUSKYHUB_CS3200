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




# ============================================
# PUT /students/{id}
# Update student profile/status
# ============================================
"""
    Update student profile, verification, or account status
    Used by: [Tim-2, Tim-5, Jessica-1]
"""
@students.route("/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """
    Update student record with new values for specified fields
    
    - UPDATE table_name SET column1 = value1, column2 = value2 WHERE condition
    - This modifies existing rows in the database
    - Example: UPDATE student SET bio = 'New bio', major = 'CS' WHERE stuId = 2
    
    This route dynamically builds the UPDATE query based on which fields
    are provided in the request body (bio, major, phone, etc.)
    """
    try:
        current_app.logger.info(f'PUT /students/{student_id} - Updating student')
        data = request.get_json()
        cursor = db.get_db().cursor()
        
        update_fields = []
        params = []
        allowed_fields = ['bio', 'major', 'phone', 'profilePhotoUrl', 
                          'verifiedStatus', 'accountStatus']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
        
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
        
        params.append(student_id)
        query = f"UPDATE student SET {', '.join(update_fields)} WHERE stuId = %s"
        
        cursor.execute(query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Student updated successfully"}), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/{id}/ratings
# Return student's average rating
# ============================================
"""
    Get provider's average rating
    Used by: [Tim-4, Emma-2]
"""
@students.route("/<int:student_id>/ratings", methods=["GET"])
def get_student_ratings(student_id):

    try:
        current_app.logger.info(f'GET /students/{student_id}/ratings')
        cursor = db.get_db().cursor()
        
        query = """
            SELECT 
                provider.stuID AS providerId,
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
        rating_data = cursor.fetchone()
        cursor.close()
        
        if not rating_data:
            return jsonify({"error": "No ratings found"}), 404
            
        return jsonify(rating_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/{id}/metrics
# Return provider performance dashboard
# ============================================
"""
    Provider metrics: bookings, services, rating, earnings
    Used by: [Jessica-6]
"""
@students.route("/<int:student_id>/metrics", methods=["GET"])
def get_student_metrics(student_id):
    try:
        cursor = db.get_db().cursor()
        
        query = """
            SELECT 
                s.stuId,
                CONCAT(s.firstName, ' ', s.lastName) AS provider_name,
                COUNT(DISTINCT t.transactId) AS total_bookings,
                COUNT(DISTINCT CASE WHEN t.transactStatus = 'completed' THEN t.transactId END) AS completed_services,
                AVG(r.rating) AS avg_rating,
                SUM(CASE WHEN t.transactStatus = 'completed' THEN t.paymentAmt ELSE 0 END) AS total_earnings
            FROM student s
            LEFT JOIN listing l ON s.stuId = l.providerId
            LEFT JOIN transact t ON l.listingId = t.listId
            LEFT JOIN review r ON l.listingId = r.listId
            WHERE s.stuId = %s
            GROUP BY s.stuId, s.firstName, s.lastName
        """
        
        cursor.execute(query, (student_id,))
        metrics = cursor.fetchone()
        cursor.close()
        
        if not metrics:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify(metrics), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/provider/metrics
# Return all providers with metrics
# ============================================
"""
    All providers with performance metrics
    Used by: [Chris-4, Chris-5]
"""
@students.route("/provider/metrics", methods=["GET"])
def get_provider_metrics():
    """
    Get all providers with their performance metrics
    Query params: sortBy (rating or transactions), limit (number of results)
    """
    try:
        sort_by = request.args.get("sortBy", "transactions")
        limit = int(request.args.get("limit", "100"))
        
        cursor = db.get_db().cursor()
        
        # This specific CASE statement:
        # CASE WHEN t.transactStatus = 'completed' THEN t.transactId END
        # 
        # Meaning: 
        # - IF transactStatus = 'completed', return the transactId
        # - ELSE (if not completed), return NULL
        query = """
            SELECT 
                s.stuId,
                s.firstName,
                s.lastName,
                s.email,
                s.campus,
                AVG(r.rating) AS avg_rating,
                COUNT(DISTINCT CASE WHEN t.transactStatus = 'completed' THEN t.transactId END) AS completed_transactions
            FROM student s
            LEFT JOIN listing l ON s.stuId = l.providerId
            LEFT JOIN transact t ON l.listingId = t.listId
            LEFT JOIN review r ON l.listingId = r.listId
            GROUP BY s.stuId, s.firstName, s.lastName, s.email, s.campus
            HAVING completed_transactions > 0
        """
        
        if sort_by == "rating":
            query += " ORDER BY avg_rating DESC"
        else:
            query += " ORDER BY completed_transactions DESC"
        
        query += f" LIMIT {limit}"
        
        cursor.execute(query)
        metrics = cursor.fetchall()
        cursor.close()
        
        return jsonify(metrics), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/consumer/metrics
# Return consumer-side metrics
# ============================================
"""
    Students as consumers/buyers
    Used by: [Chris-4]
"""
@students.route("/consumer/metrics", methods=["GET"])
def get_consumer_metrics():
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                s.stuId,
                s.firstName,
                s.lastName,
                s.email,
                s.campus,
                COUNT(t.transactId) AS transaction_count
            FROM student s
            LEFT JOIN transact t ON s.stuId = t.buyerId
            GROUP BY s.stuId, s.firstName, s.lastName, s.email, s.campus
            HAVING transaction_count > 0
            ORDER BY transaction_count DESC
        """
        
        cursor.execute(query)
        metrics = cursor.fetchall()
        cursor.close()
        
        return jsonify(metrics), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/new-user-metrics
# Returns new user activity
# ============================================
"""
    New user onboarding metrics
    Used by: [Chris-6]
"""
@students.route("/new-user-metrics", methods=["GET"])
def get_new_user_metrics():
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                s.stuId, 
                s.firstName, 
                s.lastName, 
                s.campus, 
                s.joinDate,
                (
                    SELECT MIN(l.createDate)
                    FROM listing AS l
                    WHERE l.providerId = s.stuId
                      AND l.createDate >= s.joinDate
                      AND DATEDIFF(l.createDate, s.joinDate) <= 30
                ) AS first_listing_date,
                
                DATEDIFF(
                    (
                        SELECT MIN(l2.createDate)
                        FROM listing AS l2
                        WHERE l2.providerId = s.stuId
                          AND l2.createDate >= s.joinDate
                          AND DATEDIFF(l2.createDate, s.joinDate) <= 30
                    ),
                    s.joinDate
                ) AS days_to_first_listing
            
            FROM student AS s
            WHERE DATEDIFF(NOW(), s.joinDate) <= 90
            ORDER BY s.joinDate DESC
        """
        
        cursor.execute(query)
        new_user_data = cursor.fetchall()
        cursor.close()
        
        return jsonify(new_user_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500
