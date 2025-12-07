from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create Blueprint for student routes
students = Blueprint("students", __name__)


# ============================================
# GET /students
# Return list of students searchable and filterable
# Used by: [Tim-6, Emma-2, Chris-1]
# ============================================
@students.route("/", methods=["GET"])
def get_all_students():
    """
    Get all students with optional filters
    Query params:
    - q: search term (firstName, lastName, email, phone)
    - status: filter by accountStatus (active, suspended, deleted)
    - sortBy: sort by (status, joinDate, lastName)
    - campus: filter by campus
    """
    try:
        current_app.logger.info('GET /students - Getting all students')
        
        # Get query parameters
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
        
        # Add search filter if provided
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
        
        # Add status filter if provided
        if status:
            query += " AND accountStatus = %s"
            params.append(status)
        
        # Add campus filter if provided
        if campus:
            query += " AND campus = %s"
            params.append(campus)
        
        # Add sorting
        if sort_by == "status":
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
            query += " ORDER BY joinDate DESC"
        else:
            query += " ORDER BY lastName, firstName"
        
        cursor.execute(query, params)
        students_data = cursor.fetchall()
        cursor.close()
        
        current_app.logger.info(f'Successfully retrieved {len(students_data)} students')
        return jsonify(students_data), 200
        
    except Error as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/{id}
# Return detailed student profile
# Used by: [Tim-6, Emma-2, Jessica-1]
# ============================================
@students.route("/<int:student_id>", methods=["GET"])
def get_student_profile(student_id):
    """Get detailed student profile with services and ratings"""
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
        profile = cursor.fetchone()
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
# Used by: [Tim-2, Tim-5, Jessica-1]
# ============================================
@students.route("/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """
    Update student record with new values for specified fields
    Dynamically builds UPDATE query based on provided fields
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
# Used by: [Tim-4, Emma-2]
# ============================================
@students.route("/<int:student_id>/ratings", methods=["GET"])
def get_student_ratings(student_id):
    """Get provider's average rating across all their listings"""
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
# PUT /students/{id}/suspend
# Suspend a student account
# Used by: [Tim-5]
# ============================================
@students.route("/<int:student_id>/suspend", methods=["PUT"])
def suspend_student(student_id):
    """Tim-5: Suspend a student account"""
    try:
        cursor = db.get_db().cursor()
        
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
# PUT /students/{id}/unsuspend
# Unsuspend a student account
# ============================================
@students.route("/<int:student_id>/unsuspend", methods=["PUT"])
def unsuspend_student(student_id):
    """Unsuspend a student account"""
    try:
        cursor = db.get_db().cursor()
        
        query = """
            UPDATE student
            SET accountStatus = 'active'
            WHERE stuId = %s
        """
        
        cursor.execute(query, (student_id,))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({"message": "Student unsuspended successfully"}), 200
        
    except Error as e:
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/{id}/metrics
# Return provider performance dashboard
# Used by: [Jessica-6]
# ============================================
@students.route("/<int:student_id>/metrics", methods=["GET"])
def get_student_metrics(student_id):
    """
    Jessica-6: Return provider performance dashboard metrics
    As a service provider, I want to track my performance
    """
    try:
        current_app.logger.info(f'Getting metrics for student {student_id}')
        cursor = db.get_db().cursor()
        
        query = """
            SELECT 
                s.stuId,
                CONCAT(s.firstName, ' ', s.lastName) AS provider_name,
                COUNT(DISTINCT l.listingId) AS total_services_offered,
                COUNT(DISTINCT CASE WHEN l.listingStatus = 'active' 
                      THEN l.listingId END) AS active_services,
                COUNT(DISTINCT t.transactId) AS total_bookings,
                COUNT(DISTINCT CASE WHEN t.transactStatus = 'completed' 
                      THEN t.transactId END) AS completed_bookings,
                COALESCE(SUM(CASE WHEN t.transactStatus = 'completed' 
                             THEN t.paymentAmt END), 0) AS total_earnings,
                ROUND(AVG(r.rating), 2) AS average_rating,
                COUNT(r.reviewId) AS total_reviews
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
        current_app.logger.error(f'Error getting metrics: {str(e)}')
        return jsonify({"error": str(e)}), 500


# ============================================
# GET /students/provider/metrics
# Return all providers with metrics
# Used by: [Chris-4, Chris-5]
# ============================================
@students.route("/provider/metrics", methods=["GET"])
def get_all_provider_metrics():
    """
    Get all providers with their performance metrics
    Query params: 
    - sortBy: 'rating' or 'transactions' (default)
    - limit: number of results (default 100)
    """
    try:
        sort_by = request.args.get("sortBy", "transactions")
        limit = int(request.args.get("limit", "100"))
        
        cursor = db.get_db().cursor()
        
        query = """
            SELECT 
                s.stuId,
                s.firstName,
                s.lastName,
                s.email,
                s.campus,
                AVG(r.rating) AS avg_rating,
                COUNT(DISTINCT CASE WHEN t.transactStatus = 'completed' 
                      THEN t.transactId END) AS completed_transactions
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
# Used by: [Chris-4]
# ============================================
@students.route("/consumer/metrics", methods=["GET"])
def get_consumer_metrics():
    """Get students as consumers/buyers with transaction counts"""
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
# Used by: [Chris-6]
# ============================================
@students.route("/new-user-metrics", methods=["GET"])
def get_new_user_metrics():
    """Get new user onboarding metrics (first 90 days)"""
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
