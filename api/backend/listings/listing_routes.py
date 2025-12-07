from flask import Blueprint, request, jsonify
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create listings blueprint
listings = Blueprint("listings", __name__)


# ============================================
# GET /listings
# Return all listings with filters
# [Tim-1, Emma-1, Emma-5, Jessica-2]
# ============================================
@listings.route("/", methods=["GET"])
def get_listings():
    """
    Get all listings with comprehensive details
    Query params:
    - status: Filter by listingStatus (active, inactive, removed)
    - categoryId: Filter by category
    - providerId: Filter by provider
    - search: Search in title and description
    """
    try:
        status = request.args.get('status')
        category_id = request.args.get('categoryId')
        provider_id = request.args.get('providerId')
        search_term = request.args.get('search')
        
        current_app.logger.info(f'Getting listings - status: {status}, category: {category_id}, provider: {provider_id}')
        
        cursor = db.get_db().cursor()
        
        query = """
            SELECT 
                l.listingId,
                l.title,
                l.description,
                l.price,
                l.unit,
                l.imageUrl,
                l.createDate,
                l.lastUpdate,
                l.listingStatus,
                c.categoryId,
                c.name AS category_name,
                c.type AS category_type,
                provider.stuId AS provider_id,
                CONCAT(provider.firstName, ' ', provider.lastName) AS provider_name,
                provider.verifiedStatus AS provider_verified,
                ROUND(AVG(r.rating), 2) AS listing_avg_rating,
                COUNT(DISTINCT r.reviewId) AS review_count
            FROM listing l
            INNER JOIN category c ON l.categoryId = c.categoryId
            INNER JOIN student provider ON l.providerId = provider.stuId
            LEFT JOIN review r ON l.listingId = r.listId
            WHERE 1=1
        """
        
        params = []
        
        # Add filters
        if status:
            query += " AND l.listingStatus = %s"
            params.append(status)
        
        if category_id:
            query += " AND l.categoryId = %s"
            params.append(category_id)
        
        if provider_id:
            query += " AND l.providerId = %s"
            params.append(provider_id)
        
        if search_term:
            query += " AND (l.title LIKE %s OR l.description LIKE %s)"
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
        
        query += """
            GROUP BY l.listingId, l.title, l.description, l.price, l.unit, l.imageUrl,
                     l.createDate, l.lastUpdate, l.listingStatus,
                     c.categoryId, c.name, c.type,
                     provider.stuId, provider.firstName, provider.lastName, provider.verifiedStatus
            ORDER BY l.lastUpdate DESC
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        
        current_app.logger.info(f'Found {len(results)} listings')
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting listings: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# POST /listings
# Create new service offering [Jessica-2]
# ============================================
@listings.route("/", methods=["POST"])
def create_listing():
    """
    Jessica-2: Create new service offering
    As a service provider, I want to add new service offerings
    """
    try:
        data = request.get_json()
        current_app.logger.info('Creating new service listing')
        
        # Validate required fields
        required_fields = ['categoryId', 'providerId', 'title', 'description', 'price', 'unit']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            INSERT INTO listing (
                categoryId, providerId, title, description, 
                price, unit, imageUrl, lastUpdate, listingStatus
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), 'active')
        """
        
        cursor.execute(query, (
            data['categoryId'],
            data['providerId'],
            data['title'],
            data['description'],
            data['price'],
            data['unit'],
            data.get('imageUrl', '')
        ))
        
        db.get_db().commit()
        new_id = cursor.lastrowid
        cursor.close()
        
        current_app.logger.info(f'Listing created with ID: {new_id}')
        return jsonify({
            'message': 'Service listing created successfully',
            'listingId': new_id
        }), 201
        
    except Error as e:
        current_app.logger.error(f'Error creating listing: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# GET /listings/{id}
# Return detailed listing info [Tim-1, Emma-1, Emma-4, Jessica-2]
# ============================================
@listings.route("/<int:listing_id>", methods=["GET"])
def get_listing_detail(listing_id):
    """Return detailed listing info with category and provider"""
    try:
        current_app.logger.info(f'Getting listing details for {listing_id}')
        
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                l.listingId,
                l.title,
                l.description,
                l.price,
                l.unit,
                l.imageUrl,
                l.createDate,
                l.lastUpdate,
                l.listingStatus,
                c.categoryId,
                c.name AS category_name,
                c.type AS category_type,
                provider.stuId AS provider_id,
                CONCAT(provider.firstName, ' ', provider.lastName) AS provider_name,
                provider.email AS provider_email,
                provider.phone AS provider_phone,
                provider.bio AS provider_bio,
                provider.verifiedStatus AS provider_verified,
                provider.profilePhotoUrl AS provider_photo,
                ROUND(AVG(r.rating), 2) AS avg_rating,
                COUNT(DISTINCT r.reviewId) AS review_count
            FROM listing l
            INNER JOIN category c ON l.categoryId = c.categoryId
            INNER JOIN student provider ON l.providerId = provider.stuId
            LEFT JOIN review r ON l.listingId = r.listId
            WHERE l.listingId = %s
            GROUP BY l.listingId, l.title, l.description, l.price, l.unit, l.imageUrl,
                     l.createDate, l.lastUpdate, l.listingStatus,
                     c.categoryId, c.name, c.type,
                     provider.stuId, provider.firstName, provider.lastName, provider.email,
                     provider.phone, provider.bio, provider.verifiedStatus, provider.profilePhotoUrl
        """
        
        cursor.execute(query, (listing_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return jsonify({'error': 'Listing not found'}), 404
        
        return jsonify(result), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting listing detail: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# PUT /listings/{id}
# Update listing [Tim-5, Jessica-3]
# ============================================
@listings.route("/<int:listing_id>", methods=["PUT"])
def update_listing(listing_id):
    """
    Update listing details
    Jessica-3: Update hourly rates and service packages
    Tim-5: Deactivate listings when suspending users
    """
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating listing {listing_id}')
        
        cursor = db.get_db().cursor()
        
        # Build dynamic update
        update_parts = []
        values = []
        
        if 'price' in data:
            update_parts.append('price = %s')
            values.append(data['price'])
        
        if 'description' in data:
            update_parts.append('description = %s')
            values.append(data['description'])
        
        if 'title' in data:
            update_parts.append('title = %s')
            values.append(data['title'])
        
        if 'listingStatus' in data:
            update_parts.append('listingStatus = %s')
            values.append(data['listingStatus'])
        
        if 'unit' in data:
            update_parts.append('unit = %s')
            values.append(data['unit'])
        
        if 'imageUrl' in data:
            update_parts.append('imageUrl = %s')
            values.append(data['imageUrl'])
        
        # Always update lastUpdate
        update_parts.append('lastUpdate = NOW()')
        
        if not update_parts:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(listing_id)
        query = f"UPDATE listing SET {', '.join(update_parts)} WHERE listingId = %s"
        
        cursor.execute(query, values)
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Listing not found'}), 404
        
        cursor.close()
        current_app.logger.info(f'Listing {listing_id} updated successfully')
        return jsonify({'message': 'Listing updated successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error updating listing: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# DELETE /listings/{id}
# Remove listing [Jessica-3]
# ============================================
@listings.route("/<int:listing_id>", methods=["DELETE"])
def delete_listing(listing_id):
    """
    Jessica-3: Remove/deactivate service offering
    As a service provider, I want to remove outdated services
    """
    try:
        current_app.logger.info(f'Removing listing {listing_id}')
        
        cursor = db.get_db().cursor()
        query = """
            UPDATE listing
            SET listingStatus = 'removed',
                lastUpdate = NOW()
            WHERE listingId = %s
        """
        
        cursor.execute(query, (listing_id,))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Listing not found'}), 404
        
        cursor.close()
        current_app.logger.info(f'Listing {listing_id} removed successfully')
        return jsonify({'message': 'Listing removed successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error removing listing: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# GET /listings/{id}/availability
# Return available time slots [Emma-3, Jessica-4]
# ============================================
@listings.route("/<int:listing_id>/availability", methods=["GET"])
def get_listing_availability(listing_id):
    """
    Return available time slots for a listing
    Emma-3: View provider availability calendars
    Jessica-4: View my availability slots
    """
    try:
        current_app.logger.info(f'Getting availability for listing {listing_id}')
        
        cursor = db.get_db().cursor()
        query = """
            SELECT 
                a.availabilityId,
                a.startTime,
                a.endTime,
                l.title AS service_name,
                CONCAT(s.firstName, ' ', s.lastName) AS provider_name
            FROM availability a
            JOIN listing l ON a.listId = l.listingId
            JOIN student s ON l.providerId = s.stuId
            WHERE l.listingId = %s AND a.startTime > NOW()
            ORDER BY a.startTime ASC
        """
        
        cursor.execute(query, (listing_id,))
        results = cursor.fetchall()
        cursor.close()
        
        return jsonify(results), 200
        
    except Error as e:
        current_app.logger.error(f'Error getting availability: {str(e)}')
        return jsonify({'error': str(e)}), 500


# ============================================
# POST /listings/{id}/availability
# Create availability blocks [Jessica-4]
# ============================================
@listings.route("/<int:listing_id>/availability", methods=["POST"])
def add_availability(listing_id):
    """
    Jessica-4: Create recurring availability blocks
    As a service provider, I want to set recurring availability blocks
    """
    try:
        data = request.get_json()
        current_app.logger.info(f'Adding availability for listing {listing_id}')
        
        if 'slots' not in data or not isinstance(data['slots'], list):
            return jsonify({'error': 'slots array required in request body'}), 400
        
        if len(data['slots']) == 0:
            return jsonify({'error': 'At least one slot required'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            INSERT INTO availability (listId, startTime, endTime)
            VALUES (%s, %s, %s)
        """
        
        for slot in data['slots']:
            if 'startTime' not in slot or 'endTime' not in slot:
                return jsonify({'error': 'Each slot must have startTime and endTime'}), 400
            
            cursor.execute(query, (
                listing_id,
                slot['startTime'],
                slot['endTime']
            ))
        
        db.get_db().commit()
        cursor.close()
        
        current_app.logger.info(f'{len(data["slots"])} availability slots created')
        return jsonify({
            'message': f'{len(data["slots"])} availability slots created successfully'
        }), 201
        
    except Error as e:
        current_app.logger.error(f'Error adding availability: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# PUT /listings/{id}/availability/{availability_id}
# Update availability slot [Jessica-4]
# ============================================
@listings.route("/<int:listing_id>/availability/<int:availability_id>", methods=["PUT"])
def update_availability(listing_id, availability_id):
    """
    Jessica-4: Update existing availability slot times
    As a service provider, I want to update my availability
    """
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating availability {availability_id}')
        
        if 'startTime' not in data or 'endTime' not in data:
            return jsonify({'error': 'startTime and endTime required'}), 400
        
        cursor = db.get_db().cursor()
        query = """
            UPDATE availability
            SET startTime = %s,
                endTime = %s
            WHERE availabilityId = %s AND listId = %s
        """
        
        cursor.execute(query, (
            data['startTime'],
            data['endTime'],
            availability_id,
            listing_id
        ))
        
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Availability slot not found'}), 404
        
        cursor.close()
        return jsonify({'message': 'Availability updated successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error updating availability: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500


# ============================================
# DELETE /listings/{id}/availability/{availability_id}
# Remove availability slot [Jessica-4]
# ============================================
@listings.route("/<int:listing_id>/availability/<int:availability_id>", methods=["DELETE"])
def delete_availability(listing_id, availability_id):
    """
    Jessica-4: Remove/cancel specific available time slot
    As a service provider, I want to remove availability slots
    """
    try:
        current_app.logger.info(f'Deleting availability {availability_id}')
        
        cursor = db.get_db().cursor()
        query = """
            DELETE FROM availability
            WHERE availabilityId = %s AND listId = %s
        """
        
        cursor.execute(query, (availability_id, listing_id))
        db.get_db().commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Availability slot not found'}), 404
        
        cursor.close()
        return jsonify({'message': 'Availability slot removed successfully'}), 200
        
    except Error as e:
        current_app.logger.error(f'Error deleting availability: {str(e)}')
        db.get_db().rollback()
        return jsonify({'error': str(e)}), 500
