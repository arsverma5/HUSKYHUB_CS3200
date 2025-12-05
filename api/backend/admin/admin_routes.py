from flask import Blueprint, request, jsonify
from backend.db_connection import db

admins = Blueprint('admins', __name__)

# ---------------
# REPORTS ROUTES
# ---------------

# User story 3.1: 
@admins.route("/reports", methods=["GET"])
def get_all_reports():
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                r.reportId,
                r.reason,
                reported.stuId AS reported_student_id,
                CASE
                    WHEN reported.accountStatus = 'suspended' THEN 'URGENT'
                    WHEN l.listingId IS NOT NULL AND l.listingStatus = 'active' THEN 'HIGH'
                    WHEN DATEDIFF(CURRENT_TIMESTAMP, r.reportDate) > 7 THEN 'HIGH'
                    ELSE 'MEDIUM'
                END AS priority 
            FROM report r
            JOIN student reporter ON r.reportingStuId = reporter.stuId
            JOIN student reported ON r.reportedStuId = reported.stuId
            LEFT JOIN listing l ON r.reportedListingId = l.listingId
            WHERE r.resolutionDate IS NULL
            ORDER BY
                CASE
                    WHEN reported.accountStatus = 'suspended' THEN 1
                    WHEN l.listingId IS NOT NULL AND l.listingStatus = 'active' THEN 2
                    WHEN DATEDIFF(CURRENT_TIMESTAMP, r.reportDate) > 7 THEN 2
                    ELSE 3
                END,
                r.reportDate DESC
        """
        cursor.execute(query)
        reports = cursor.fetchall()
        cursor.close()
        return jsonify(reports), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# User Story 3.1
@admins.route("/reports/<int:report_id>", methods=["GET"])
def get_report_by_id(report_id):
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT
                r.reportId,
                r.reportDate,
                r.resolutionDate,
                r.reason,
                r.reportDetails,
                reporter.stuId AS reporter_id,
                reporter.firstName AS reporter_fname,
                reporter.lastName AS reporter_lname,
                reporter.email AS reporter_email,
                reporter.accountStatus AS reporter_account_status,
                reported.stuId AS reported_student_id,
                reported.firstName AS reported_fname,
                reported.lastName AS reported_lname,
                reported.email AS reported_email,
                reported.accountStatus AS reported_account_status,
                l.listingId AS reported_listing_id,
                l.title AS listing_title,
                l.listingStatus,
                c.name AS category_name,
                CASE
                    WHEN reported.accountStatus = 'suspended' THEN 'URGENT'
                    WHEN l.listingId IS NOT NULL AND l.listingStatus = 'active' THEN 'HIGH'
                    WHEN DATEDIFF(CURRENT_TIMESTAMP, r.reportDate) > 7 THEN 'HIGH'
                    ELSE 'MEDIUM'
                END AS priority
            FROM report r
            JOIN student reporter ON r.reportingStuId = reporter.stuId
            JOIN student reported ON r.reportedStuId = reported.stuId
            LEFT JOIN listing l ON r.reportedListingId = l.listingId
            LEFT JOIN category c ON l.categoryId = c.categoryId
            WHERE r.reportId = %s
        """
        cursor.execute(query, (report_id,))
        report = cursor.fetchone()
        cursor.close()
        
        if report is None:
            return jsonify({"error": "Report not found"}), 404
        
        return jsonify(report), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# User Story 3.1 - Update/resolve a report
@admins.route("/reports/<int:report_id>", methods=["PUT"])
def update_report(report_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        # Check if report exists
        cursor.execute("SELECT * FROM report WHERE reportId = %s", (report_id,))
        report = cursor.fetchone()
        
        if report is None:
            cursor.close()
            return jsonify({"error": "Report not found"}), 404
        
        # Update the report with resolution
        query = """
            UPDATE report
            SET resolutionDate = CURRENT_TIMESTAMP,
                reportDetails = %s
            WHERE reportId = %s
        """
        
        resolution_notes = data.get("resolution_notes", "Resolved by admin")
        
        cursor.execute(query, (resolution_notes, report_id))
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Report resolved successfully",
            "reportId": report_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#-------------------
# SUSPENSION ROUTES
#------------------

# User story 3.5 - get all suspensions
@admins.route("/suspensions", methods=["GET"])
def get_all_suspensions():
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT
                s.suspensionId,
                s.type
                s.startDate,
                s.endDate,
                st.firstName,
                st.lastName,
                st.email,
                st.accountStatus
                r.reportId,
                r.reason AS report reason,
                CASE
                    WHEN s.endDate IS NULL THEN 'PERMANENT'
                    WEHN s.ednDate < CURRENT_TIMESTAMP THEN 'EXPIRED'
                    ELSE 'ACTIVE'
                END AS status
                FROM suspension s
                JOIN student st ON s.stuId = st.stuId
                LEFT JOIN report r ON s.reportId = r.reportId
                ORDER BY s.startDate DESC
        """
        cursor.execute(query)
        suspensions = cursor.fetchall()
        cursor.close()
        return jsonify(suspensions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# User story 3.5 - create a new suspension
@admins.route("/suspensions", methods=['POST'])
def create_suspension():
    try:
        data = request.get_json()
        # required fields
        stu_id = data.get("studId")
        suspension_type = data.get("type", "temporary") #temporary or permanent
        # optional fields
        report_id = data.get("reportId")
        end_date = data.get("endDate") #NULL for permanent
        if not stu_id:
            return jsonify({"error": "stuId is required"}), 400
        
        cursor = db.get_db().cursor()

        cursor.execute("SELECT * FROM student WHERE studId = %s", (stu_id,))
        student = cursor.fetchone()
        
        if student is None:
            cursor.close()
            return jsonify({"error": "Student not found"}), 404
        
        #create suspension record
        insert_query = """
            INSERT INTO suspension (stuId, reportId, type, startDate, endDate)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
        """
        cursor.execute(insert_query, (stu_id, report_id, suspension_type, end_date))

        #update student acct status to suspended
        cursor.execute(
            "UPDATE student SET accountStatus = 'suspended' WHERE stuId = %s",
            (stu_id,)
        )

        #deactivate all listings by that acct
        cursor.execute(
            "UPDATE listing SET listingStatus = 'removed' WHERE providerId = %s AND listingStatus = 'active'",
            (stu_id,)
        )

        #Cancel all pending transactions
        cursor.execute("""
                       UPDATE transact t
                       JOIN listing l ON t.listId = l.listingId
                       SET t.transactStatus = 'cancelled'
                       WHERE l.providerId = %s AND t.transactStatus IN ('requested', 'confirmed')
                       """, (stu_id,))
        
        db.get_db().commit()

        #get the new suspension ID
        suspension_id = cursor.lastrowid
        cursor.close()

        return jsonify({
            "message": "Suspension created succesfully",
            "suspensionId": suspension_id
        }), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# User story 3.5 - get a specific suspension by id
@admins.route("/suspensions/<int:suspension_id>", methods=["GET"])
def get_suspension_by_id(suspension_id):
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT
                s.suspensionId,
                s.type,
                s.startDate,
                s.endDate,
                s.stuId,
                st.firstName,
                st.lastName,
                st.email,
                st.accountStatus,
                st.phone,
                r.reportId,
                r.reason AS report_reason,
                r.reportDate,
                r.reportDetails,
                CASE
                    WHEN s.endDate IS NULL THEN 'PERMANENT'
                    WHEN s.endDate < CURRENT_TIMESTAMP THEN 'EXPIRED'
                    ELSE 'ACTIVE'
                END AS status,
                DATEDIFF(s.endDate, CURRENT_TIMESTAMP) AS days_remaining
            FROM suspension s
            JOIN student st ON s.stuId = st.stuID
            LEFT JOIN report r ON s.reportId = r.reportId
            WHERE s.suspensionId = %s
        """
        cursor.execute(query, (suspension_id))
        suspension = cursor.fetchone()
        cursor.close()

        if suspension is None:
            return jsonify({"error": "Suspension not found"}), 404
        
        return jsonify(suspension), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#User story 3.5 - update a suspension (extend endDate, change type)
@admins.route("/suspensions/<int:suspension_id>", methods=["PUT"])
def update_suspension(suspension_id):
    try:
        data = request.get_json()
        
        cursor = db.get_db().cursor()
        
        # Check if suspension exists
        cursor.execute("SELECT * FROM suspension WHERE suspensionId = %s", (suspension_id,))
        suspension = cursor.fetchone()
        
        if suspension is None:
            cursor.close()
            return jsonify({"error": "Suspension not found"}), 404
        
        # Build update query based on provided fields
        updates = []
        params = []
        
        if "endDate" in data:
            updates.append("endDate = %s")
            params.append(data["endDate"])
        
        if "type" in data:
            if data["type"] not in ["temporary", "permanent"]:
                cursor.close()
                return jsonify({"error": "Type must be 'temporary' or 'permanent'"}), 400
            updates.append("type = %s")
            params.append(data["type"])
            
            # If changing to permanent, set endDate to NULL
            if data["type"] == "permanent":
                updates.append("endDate = NULL")
        
        if not updates:
            cursor.close()
            return jsonify({"error": "No valid fields to update"}), 400
        
        # Execute update
        query = f"UPDATE suspension SET {', '.join(updates)} WHERE suspensionId = %s"
        params.append(suspension_id)
        
        cursor.execute(query, params)
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Suspension updated successfully",
            "suspensionId": suspension_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# user story 3.5 - remove a suspension early
@admins.route("/suspensions/<int:suspension_id>", methods=["DELETE"])
def lift_suspension(suspension_id):
    try:
        cursor = db.get_db().cursor()
        
        # Get suspension details
        cursor.execute("""
            SELECT s.*, st.stuId 
            FROM suspension s 
            JOIN student st ON s.stuId = st.stuId 
            WHERE s.suspensionId = %s
        """, (suspension_id,))
        suspension = cursor.fetchone()
        
        if suspension is None:
            cursor.close()
            return jsonify({"error": "Suspension not found"}), 404
        
        stu_id = suspension["stuId"]
        
        # Option 1: Delete the suspension record
        # cursor.execute("DELETE FROM suspension WHERE suspensionId = %s", (suspension_id,))
        
        # Option 2: Set endDate to now (keeps record for history)
        cursor.execute(
            "UPDATE suspension SET endDate = CURRENT_TIMESTAMP WHERE suspensionId = %s",
            (suspension_id,)
        )
        
        # Check if student has any other active suspensions
        cursor.execute("""
            SELECT COUNT(*) as active_count 
            FROM suspension 
            WHERE stuId = %s 
            AND suspensionId != %s
            AND (endDate IS NULL OR endDate > CURRENT_TIMESTAMP)
        """, (stu_id, suspension_id))
        result = cursor.fetchone()
        
        # Only reactivate account if no other active suspensions
        if result["active_count"] == 0:
            cursor.execute(
                "UPDATE student SET accountStatus = 'active' WHERE stuId = %s",
                (stu_id,)
            )
        
        db.get_db().commit()
        cursor.close()
        
        return jsonify({
            "message": "Suspension lifted successfully",
            "suspensionId": suspension_id,
            "stuId": stu_id
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
