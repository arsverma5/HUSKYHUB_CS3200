from flask import Blueprint, jsonify, request
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create Blueprint
transactions = Blueprint("transactions", __name__)

# Test route
@transactions.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "Transactions blueprint works!"}), 200

# Get all transactions
@transactions.route("/transactions", methods=["GET"])
def get_all_transactions():
    try:
        cursor = db.get_db().cursor()
        query = "SELECT * FROM transact LIMIT 10"
        cursor.execute(query)
        trans_data = cursor.fetchall()
        cursor.close()
        return jsonify(trans_data), 200
    except Error as e:
        return jsonify({"error": str(e)}), 500