from flask import Blueprint, request, jsonify
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create transactions blueprint
transactions = Blueprint("transactions", __name__)

# ============================================
# GET /transactions
# Return all transactions with dispute info
# [Tim-3, Emma-3, Jessica-5]
# ============================================
@transactions.route("/transactions", methods=["GET"])
def get_transactions():
    """
    Get transactions with comprehensive details including:
    - All transaction attributes
    - Buyer & seller info
    - Listing info
    - Associated availability
    - Reports and admin notes
    """
    try:
        provider_id = request.args.get('providerId')
        buyer_id = request.args.get('buyerId')
        status = request.args.get('status')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        current_app.logger.info(f'Getting transactions with filters: providerId={provider_id}, buyerId={buyer_id}, status={status}')
        
        cursor = db.get_db().cursor()
        
        # Main transaction query with all linked data
        query = """
            SELECT 
                -- Transaction attributes
                t.transactId,
                t.bookDate,
                t.transactStatus,
                t.paymentAmt,
                t.platformFee,
                t.fulfillmentDate,
                t.agreementDetails,
                
                -- Listing info
                l.listingId,
                l.title AS service_name,
                l.description AS service_description,
                l.price AS listing_price,
                l.unit,
                l.listingStatus,
                l.createDate AS listing_created,
                
                -- Buyer info
                buyer.stuId AS buyer_id,
                CONCAT(buyer.firstName, ' ', buyer.lastName) AS buyer_name,
                buyer.email AS buyer_email,
                buyer.phone AS buyer_phone,
                buyer.major AS buyer_major,
                buyer.campus AS buyer_campus,
                buyer.verifiedStatus AS buyer_verified,
                
                -- Seller/Provider info
                seller.stuId AS seller_id,
                CONCAT(seller.firstName, ' ', seller.lastName) AS seller_name,
                seller.email AS seller_email,
                seller.phone AS seller_phone,
                seller.major AS seller_major,
                seller.campus AS seller_campus,
                seller.verifiedStatus AS seller_verified,
                
                -- Category info
                c.categoryId,
                c.name AS category_name,
                c.type AS category_type,
                
                -- Availability info (next available slot for this listing)
                (SELECT MIN(a.startTime) 
                 FROM availability a 
                 WHERE a.listId = l.listingId 
                   AND a.startTime > NOW()) AS next_availability,
                
                (SELECT COUNT(*) 
                 FROM availability a 
                 WHERE a.listId = l.listingId 
                   AND a.startTime > NOW()) AS available_slots_count,
                
                -- Report info
                (SELECT COUNT(*) 
                 FROM report r 
                 WHERE r.reportedListingId = l.listingId 
                    OR r.reportedStuId = seller.stuId 
                    OR r.reportedStuId = buyer.stuId) AS total_reports,
                
                (SELECT COUNT(*) 
                 FROM report r 
                 WHERE (r.reportedListingId = l.listingId 
                        OR r.reportedStuId = seller.stuId 
                        OR r.reportedStuId = buyer.stuId)
                   AND r.resolutionDate IS NULL) AS unresolved_reports,
                
                -- Admin notes count
                (SELECT COUNT(*) 
                 FROM admin_notes an
                 INNER JOIN report r ON an.reportId = r.reportId
                 WHERE r.reportedListingId = l.listingId) AS admin_notes_count
                
            FROM transact t
            INNER JOIN listing l ON t.listId = l.listingId
            INNER JOIN category c ON l.categoryId = c.categoryId
            INNER JOIN student buyer ON t.buyerId = buyer.stuId
            LEFT JOIN student seller ON l.providerId = seller.stuId
            WHERE 1=1
        """
        
        params = []
        
        # Add filters based on query parameters
        if provider_id:
            query += " AND l.providerId = %s"
            params.append(provider_id)
        
        if buyer_id:
            query += " AND t.buyerId = %s"
            params.append(buyer_id)
        
        if status:
            query += " AND t.transactStatus = %s"
            params.append(status)
        
        if start_date and end_date:
            query += " AND DATE(t.bookDate) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND DATE(t.bookDate) >= %s"
            params.append(start_date)
        elif end_date:
            query += " AND DATE(t.bookDate) <= %s"
            params.append(end_date)
        
        query += " ORDER BY t.bookDate DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        current_app.logger.info(f'Found {len(results)} transactions')
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting transactions: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# POST /transactions
# Create new booking/transaction [Emma-3]
# As a student, I want to book appointments
# ============================================
@transactions.route("/transactions", methods=["POST"])
def create_transaction():
    """
    Emma-3: Create new booking/transaction
    """
    try:
        data = request.get_json()
        current_app.logger.info('Creating new transaction')
        
        # Validate required fields
        required_fields = ['buyerId', 'listId', 'bookDate', 'paymentAmt']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            INSERT INTO transact (
                buyerId, listId, bookDate, transactStatus, 
                paymentAmt, platformFee, agreementDetails
            )
            VALUES (%s, %s, %s, 'requested', %s, %s, %s)
        """
        
        # Calculate platform fee (e.g., 10% of payment)
        platform_fee = float(data['paymentAmt']) * 0.10
        
        cursor.execute(query, (
            data['buyerId'],
            data['listId'],
            data['bookDate'],
            data['paymentAmt'],
            platform_fee,
            data.get('agreementDetails', '')
        ))
        
        db.get_db().commit()
        new_id = cursor.lastrowid
        cursor.close()
        
        current_app.logger.info(f'Transaction created with ID: {new_id}')
        return jsonify({
            'message': 'Transaction created successfully',
            'transactId': new_id
        }), 201
        
    except Error as e:
        current_app.logger.error(f'Error creating transaction: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# GET /transactions/completion
# Returns completion rate [Chris-3]
# ============================================
@transactions.route("/transactions/completion", methods=["GET"])
def get_completion_rate():
    """
    Chris-3: Returns completion rate of all transactions
    As a PM, I want to view completion rates
    """
    try:
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                COUNT(*) AS total_transactions,
                SUM(CASE WHEN transactStatus = 'completed' THEN 1 ELSE 0 END) AS completed_transactions,
                ROUND(
                    SUM(CASE WHEN transactStatus = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
                    2
                ) AS completion_rate
            FROM transact
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'total_transactions': result[0],
            'completed_transactions': result[1],
            'completion_rate': float(result[2]) if result[2] else 0
        }), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting completion rate: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# GET /transactions/{id}
# Return detailed transaction with dispute log
# [Tim-3, Jessica-5]
# ============================================
@transactions.route("/transactions/<int:transaction_id>", methods=["GET"])
def get_transaction_detail(transaction_id):
    """
    Tim-3, Jessica-5: Return detailed transaction with full dispute log
    """
    try:
        current_app.logger.info(f'Getting transaction details for {transaction_id}')
        
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                t.transactId,
                t.bookDate,
                t.transactStatus,
                t.paymentAmt,
                t.platformFee,
                t.fulfillmentDate,
                t.agreementDetails,
                l.title AS service_name,
                l.price,
                l.listingId,
                CONCAT(buyer.firstName, ' ', buyer.lastName) AS buyer_name,
                buyer.email AS buyer_email,
                buyer.stuId AS buyer_id,
                CONCAT(seller.firstName, ' ', seller.lastName) AS seller_name,
                seller.email AS seller_email,
                seller.stuId AS seller_id
            FROM transact t
            INNER JOIN listing l ON t.listId = l.listingId
            INNER JOIN student buyer ON t.buyerId = buyer.stuId
            LEFT JOIN student seller ON l.providerId = seller.stuId
            WHERE t.transactId = %s
        """
        
        cursor.execute(query, (transaction_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Get associated reports
        report_query = """
            SELECT 
                r.reportId,
                r.reportDate,
                r.reason,
                r.reportDetails,
                r.resolutionDate,
                CONCAT(reporter.firstName, ' ', reporter.lastName) AS reporter_name
            FROM report r
            INNER JOIN student reporter ON r.reportingStuId = reporter.stuId
            WHERE r.reportedStuId IN (%s, %s)
               OR r.reportedListingId = %s
            ORDER BY r.reportDate DESC
        """
        
        cursor.execute(report_query, (result[12], result[15], result[9]))
        reports = cursor.fetchall()
        
        cursor.close()
        
        return jsonify({
            'transaction': result,
            'reports': reports
        }), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting transaction detail: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# PUT /transactions/{id}
# Update transaction status [Tim-5, Emma-3, Jessica-5]
# ============================================
@transactions.route("/transactions/<int:transaction_id>", methods=["PUT"])
def update_transaction(transaction_id):
    """
    Update transaction status
    - 'confirmed' or 'cancelled' for Jessica-5 (accept/decline)
    - 'cancelled' for Tim-5 (when suspending user)
    - Various statuses for Emma-3 (reschedule booking)
    """
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating transaction {transaction_id}')
        
        if 'transactStatus' not in data:
            return jsonify({'error': 'transactStatus required in request body'}), 400
        
        # Validate status values
        valid_statuses = ['requested', 'confirmed', 'completed', 'cancelled']
        if data['transactStatus'] not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
        
        cursor = db.get_db().cursor()
        
        # Check if we're also updating the booking date (reschedule)
        if 'bookDate' in data:
            query = """
                UPDATE transact
                SET transactStatus = %s,
                    bookDate = %s
                WHERE transactId = %s
            """
            cursor.execute(query, (data['transactStatus'], data['bookDate'], transaction_id))
        else:
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
# DELETE /transactions/{id}
# Cancel booking [Emma-3]
# ============================================
@transactions.route("/transactions/<int:transaction_id>", methods=["DELETE"])
def cancel_transaction(transaction_id):
    """
    Emma-3: Cancel booking
    As a student, I want to cancel bookings
    """
    try:
        current_app.logger.info(f'Cancelling transaction {transaction_id}')
        
        cursor = db.get_db().cursor()
        
        # Soft delete - just update status to cancelled
        query = """
            UPDATE transact
            SET transactStatus = 'cancelled'
            WHERE transactId = %s
        """
        
        cursor.execute(query, (transaction_id,))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Transaction not found'}), 404
        
        cursor.close()
        current_app.logger.info(f'Transaction {transaction_id} cancelled')
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error cancelling transaction: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# PUT /transactions/{id}/complete
# Mark service as completed [Jessica-6]
# ============================================
@transactions.route("/transactions/<int:transaction_id>/complete", methods=["PUT"])
def complete_transaction(transaction_id):
    """
    Jessica-6: Update transaction status to 'completed' and set fulfillmentDate
    As a service provider, I want to mark completed services
    """
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


# ============================================
# GET /transactions/category/{category}
# Returns transactions within a certain category [Chris-2]
# ============================================
@transactions.route("/transactions/category/<int:category_id>", methods=["GET"])
def get_transactions_by_category(category_id):
    """
    Chris-2: Returns transactions within a certain category
    As a PM, I want to see which service categories have the most transactions
    """
    try:
        current_app.logger.info(f'Getting transactions for category {category_id}')
        
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                t.transactId,
                t.bookDate,
                t.transactStatus,
                t.paymentAmt,
                l.title AS service_name,
                c.name AS category_name,
                CONCAT(buyer.firstName, ' ', buyer.lastName) AS buyer_name
            FROM transact t
            INNER JOIN listing l ON t.listId = l.listingId
            INNER JOIN category c ON l.categoryId = c.categoryId
            INNER JOIN student buyer ON t.buyerId = buyer.stuId
            WHERE c.categoryId = %s
            ORDER BY t.bookDate DESC
        """
        
        cursor.execute(query, (category_id,))
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting transactions by category: {str(e)}')
        return jsonify({'error': str(e)}), 500