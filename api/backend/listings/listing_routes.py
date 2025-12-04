from flask import Blueprint, request, jsonify
from backend.db_connection import db
from mysql.connector import Error
from flask import current_app

# Create Blueprint
listings = Blueprint("listings", __name__)

# ============================================
# USER STORY 2.2: Create new service offering
# POST /listings
# ============================================
@listings.route("/listings", methods=["POST"])
def create_listing():
    """Jessica-2: Create new service offering with title, description, price, category"""
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
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.3: Update listing price/description
# PUT /listings/{id}
# ============================================
@listings.route("/listings/<int:listing_id>", methods=["PUT"])
def update_listing(listing_id):
    """Jessica-3: Update listing status to 'removed' and lastUpdate timestamp"""
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating listing {listing_id}')
        
        cursor = db.get_db().cursor()
        
        # Build dynamic update based on what's provided
        update_parts = []
        values = []
        
        if 'price' in data:
            update_parts.append('price = %s')
            values.append(data['price'])
        
        if 'description' in data:
            update_parts.append('description = %s')
            values.append(data['description'])
        
        if 'listingStatus' in data:
            update_parts.append('listingStatus = %s')
            values.append(data['listingStatus'])
        
        # Always update lastUpdate
        update_parts.append('lastUpdate = NOW()')
        
        if not update_parts:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Add listing_id to values for WHERE clause
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
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.3: Remove service offering
# DELETE /listings/{id}
# ============================================
@listings.route("/listings/<int:listing_id>", methods=["DELETE"])
def delete_listing(listing_id):
    """Jessica-3: Remove/deactivate service offering by changing listingStatus to 'removed'"""
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
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.4: Add availability slots
# POST /listings/{id}/availability
# ============================================
@listings.route("/listings/<int:listing_id>/availability", methods=["POST"])
def add_availability(listing_id):
    """Jessica-4: Create recurring availability blocks with startTime and endTime"""
    try:
        data = request.get_json()
        current_app.logger.info(f'Adding availability for listing {listing_id}')
        
        if 'slots' not in data or not isinstance(data['slots'], list):
            return jsonify({'error': 'slots array required in request body'}), 400
        
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
# USER STORY 2.4: Update availability slot
# PUT /listings/{id}/availability
# ============================================
@listings.route("/listings/<int:listing_id>/availability/<int:availability_id>", methods=["PUT"])
def update_availability(listing_id, availability_id):
    """Jessica-4: Update existing availability slot times"""
    try:
        data = request.get_json()
        current_app.logger.info(f'Updating availability {availability_id} for listing {listing_id}')
        
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
        return jsonify({'error': str(e)}), 500


# ============================================
# USER STORY 2.4: Delete availability slot
# DELETE /listings/{id}/availability
# ============================================
@listings.route("/listings/<int:listing_id>/availability/<int:availability_id>", methods=["DELETE"])
def delete_availability(listing_id, availability_id):
    """Jessica-4: Remove/cancel specific available time slot"""
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
        return jsonify({'error': str(e)}), 500