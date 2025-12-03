from flask import Blueprint, request, jsonify
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

reviews = Blueprint("reviews", __name__)

# ============================================
# USER STORY Jessica-6: Get all reviews for provider
# GET /reviews
# ============================================
@reviews.route("/reviews", methods=["GET"])
def get_reviews():
    """Jessica-6: Return all reviews for provider's listings with rating, reviewText, createDate"""
    try:
        provider_id = request.args.get('providerId')
        
        if not provider_id:
            return jsonify({'error': 'providerId parameter required'}), 400
        
        current_app.logger.info(f'Getting reviews for provider {provider_id}')
        
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                r.reviewId,
                r.rating,
                r.reviewText,
                r.createDate,
                CONCAT(s.firstName, ' ', s.lastName) AS reviewer_name,
                l.title AS service_name,
                l.listingId
            FROM review r
            INNER JOIN listing l ON r.listId = l.listingId
            INNER JOIN student s ON r.reviewerId = s.stuId
            WHERE l.providerId = %s
            ORDER BY r.createDate DESC
        """
        
        cursor.execute(query, (provider_id,))
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting reviews: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY Emma-4: Create new review
# POST /reviews
# ============================================
@reviews.route("/reviews", methods=["POST"])
def create_review():
    """Emma-4: Create new review after booking"""
    try:
        data = request.get_json()
        current_app.logger.info('Creating new review')
        
        required_fields = ['listId', 'reviewerId', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate rating is between 1-5
        if not (1 <= data['rating'] <= 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            INSERT INTO review (listId, reviewerId, rating, reviewText)
            VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            data['listId'],
            data['reviewerId'],
            data['rating'],
            data.get('reviewText', '')
        ))
        
        db.get_db().commit()
        new_id = cursor.lastrowid
        cursor.close()
        
        current_app.logger.info(f'Review created with ID: {new_id}')
        return jsonify({
            'message': 'Review created successfully',
            'reviewId': new_id
        }), 201
        
    except Error as e:
        current_app.logger.error(f'Error creating review: {str(e)}')
        return jsonify({'error': str(e)}), 500