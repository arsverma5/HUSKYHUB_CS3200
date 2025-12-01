from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create Blueprint
admins = Blueprint("admins", __name__)

# Test route
@admins.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Admin blueprint works!"}), 200

# Get all reports
@admins.route("/reports", methods=["GET"])
def get_all_reports():
    try:
        cursor = db.get_db().cursor()
        query = "SELECT * FROM report LIMIT 10"
        cursor.execute(query)
        reports_data = cursor.fetchall()
        cursor.close()
        return jsonify(reports_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500