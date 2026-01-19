# src/routes/admin.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.recipe import Recipe
from src.models.category import Category
from src.models.rating import Rating
from src.models.favorite import Favorite
from src.routes.auth import admin_required
import os
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    """Get admin dashboard statistics"""
    try:
        # Get counts
        total_users = User.query.count()
        total_recipes = Recipe.query.count()
        pending_recipes = Recipe.query.filter_by(status='pending').count()
        total_ratings = Rating.query.count()

        # Get recent recipes
        recent_recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(5).all()

        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_recipes': total_recipes,
                'pending_recipes': pending_recipes,
                'total_ratings': total_ratings
            },
            'recent_recipes': [recipe.to_dict() for recipe in recent_recipes]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500


@admin_bp.route('/recipes/pending', methods=['GET'])
@admin_required
def get_pending_recipes():
    """Get recipes pending approval"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        recipes = Recipe.query.filter_by(status='pending') \
            .order_by(Recipe.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'recipes': [recipe.to_dict() for recipe in recipes.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': recipes.total,
                'pages': recipes.pages,
                'has_next': recipes.has_next,
                'has_prev': recipes.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch pending recipes'}), 500


@admin_bp.route('/recipes/<int:recipe_id>/approve', methods=['POST'])
@admin_required
def approve_recipe(recipe_id):
    """Approve a recipe"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        recipe.status = 'approved'
        db.session.commit()

        return jsonify({
            'message': 'Recipe approved successfully',
            'recipe': recipe.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to approve recipe'}), 500


@admin_bp.route('/recipes/<int:recipe_id>/reject', methods=['POST'])
@admin_required
def reject_recipe(recipe_id):
    """Reject/unapprove a recipe"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        recipe.status = 'rejected'
        db.session.commit()

        return jsonify({
            'message': 'Recipe rejected successfully',
            'recipe': recipe.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reject recipe'}), 500


@admin_bp.route('/recipes/<int:recipe_id>/delete', methods=['DELETE'])
@admin_required
def delete_recipe(recipe_id):
    """Delete a recipe (admin only)"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)

        # Delete associated image file if exists
        if recipe.image_filename:
            image_path = os.path.join('src/static/uploads', recipe.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete recipe (cascading will handle ratings and favorites)
        db.session.delete(recipe)
        db.session.commit()

        return jsonify({'message': 'Recipe deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete recipe'}), 500


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        users = User.query.order_by(User.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch users'}), 500


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def toggle_user_role(user_id):
    """Toggle user role between user and admin"""
    try:
        user = User.query.get_or_404(user_id)

        # Don't allow changing own role
        if user.id == session['user_id']:
            return jsonify({'error': 'Cannot change your own role'}), 400

        # Toggle role
        user.role = 'admin' if user.role == 'user' else 'user'
        db.session.commit()

        return jsonify({
            'message': f'User role changed to {user.role}',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change user role'}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)

        if user.id == session['user_id']:
            return jsonify({'error': 'Cannot delete your own account'}), 400

        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500


@admin_bp.route('/categories', methods=['POST'])
@admin_required
def add_category():
    """Add a new category"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return jsonify({'error': 'Category name is required'}), 400

        # Check if category already exists
        if Category.query.filter_by(name=name).first():
            return jsonify({'error': 'Category already exists'}), 400

        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()

        return jsonify({
            'message': 'Category added successfully',
            'category': category.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add category'}), 500


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)

        # Check if category has recipes
        if category.recipes:
            return jsonify({'error': 'Cannot delete category with existing recipes'}), 400

        db.session.delete(category)
        db.session.commit()

        return jsonify({'message': 'Category deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete category'}), 500


@admin_bp.route('/password-resets', methods=['GET'])
@admin_required
def get_password_resets():
    """Get recent password reset requests for admin visibility"""
    try:
        # Get users who have requested password reset recently or have reset it
        from sqlalchemy import or_
        users_with_resets = User.query.filter(
            or_(
                User.last_password_reset.isnot(None),
                User.reset_requested_at.isnot(None)
            )
        ).order_by(
            # Sort by the most recent of the two dates
            db.case(
                (User.last_password_reset > User.reset_requested_at, User.last_password_reset),
                else_=User.reset_requested_at
            ).desc()
        ).limit(50).all()
        
        reset_logs = []
        for user in users_with_resets:
            # Determine status
            status = 'Completed'
            if user.reset_token and user.reset_token_expiry > datetime.utcnow():
                status = 'Pending'
            elif user.reset_token:
                status = 'Expired'
                
            reset_logs.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'last_reset': user.last_password_reset.isoformat() if user.last_password_reset else None,
                'requested_at': user.reset_requested_at.isoformat() if user.reset_requested_at else None,
                'status': status,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            'password_resets': reset_logs,
            'total': len(reset_logs)
        }), 200
        
    except Exception as e:
        print(f"Error fetching password resets: {e}")
        return jsonify({'error': 'Failed to fetch password reset logs'}), 500