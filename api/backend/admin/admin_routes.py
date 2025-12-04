from flask import Blueprint, request, jsonify
from backend.db_connection import db

admins = Blueprint('admins', __name__)

# User story 3.1: 
@admins.route("/reports", methods=["GET"])
def get_all_reports():
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                r.reportId,
                r.reason,
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

# User Story 3.1  
# Update/resolve a report
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