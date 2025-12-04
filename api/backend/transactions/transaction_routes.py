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


# ============================================
# USER STORY 2.5: View pending service requests
# GET /transactions
# ============================================
@transactions.route("/transactions", methods=["GET"])
def get_transactions():
    """Jessica-5: Return all transactions with dispute info, buyer/seller details"""
    try:
        provider_id = request.args.get('providerId')
        status_filter = request.args.get('status')  # Optional filter
        
        current_app.logger.info(f'Getting transactions for provider {provider_id}')
        
        cursor = db.get_db().cursor()
        
        if provider_id:
            # Get transactions for specific provider
            query = """
                SELECT 
                    t.transactId,
                    t.bookDate,
                    t.transactStatus,
                    t.paymentAmt,
                    l.title AS service_name,
                    l.price,
                    l.unit,
                    CONCAT(s.firstName, ' ', s.lastName) AS student_name,
                    s.email AS student_email,
                    s.phone AS student_phone,
                    t.agreementDetails
                FROM transact t
                INNER JOIN listing l ON t.listId = l.listingId
                INNER JOIN student s ON t.buyerId = s.stuId
                WHERE l.providerId = %s
            """
            
            params = [provider_id]
            
            if status_filter:
                query += " AND t.transactStatus = %s"
                params.append(status_filter)
            
            query += " ORDER BY t.bookDate ASC"
            
            cursor.execute(query, params)
        else:
            # Get all transactions (for admin/analytics)
            query = """
                SELECT 
                    t.transactId,
                    t.bookDate,
                    t.transactStatus,
                    t.paymentAmt,
                    l.title,
                    CONCAT(buyer.firstName, ' ', buyer.lastName) AS buyer_name,
                    CONCAT(seller.firstName, ' ', seller.lastName) AS seller_name
                FROM transact t
                INNER JOIN listing l ON t.listId = l.listingId
                INNER JOIN student buyer ON t.buyerId = buyer.stuId
                LEFT JOIN student seller ON l.providerId = seller.stuId
                ORDER BY t.bookDate DESC
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting transactions: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.5: Accept or decline booking request
# PUT /transactions/{id}
# ============================================
@transactions.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    """Jessica-5: Update transaction status to 'confirmed' or 'cancelled'"""
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating transaction {transaction_id}')
        
        if 'transactStatus' not in data:
            return jsonify({'error': 'transactStatus required in request body'}), 400
        
        # Validate status values
        valid_statuses = ['confirmed', 'cancelled', 'requested', 'completed']
        if data['transactStatus'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            UPDATE transact
            SET transactStatus = %s
            WHERE transactId = %s
        """
        
        cursor.execute(query, (data['transactStatus'], transaction_id))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Transaction not found'}), 404
        
        cursor.close()
        current_app.logger.info(f'Transaction {transaction_id} status updated to {data["transactStatus"]}')
        return jsonify({'message': f'Transaction {data["transactStatus"]} successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error updating transaction: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.6: Mark service as completed
# PUT /transactions/{id}/complete
# ============================================
@transactions.route("/transactions/<int:transaction_id>/complete", methods=["PUT"])
def complete_transaction(transaction_id):
    """Jessica-6: Update transaction status to 'completed' and set fulfillmentDate"""
    try:
        current_app.logger.info(f'Completing transaction {transaction_id}')
        
        cursor = db.get_db().cursor()
        query = """
            UPDATE transact
            SET transactStatus = 'completed',
                fulfillmentDate = NOW()
            WHERE transactId = %s
        """
        
        cursor.execute(query, (transaction_id,))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Transaction not found'}), 404
        
        cursor.close()
        current_app.logger.info(f'Transaction {transaction_id} marked as completed')
        return jsonify({'message': 'Transaction marked as completed successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error completing transaction: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500