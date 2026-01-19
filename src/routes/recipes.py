# src/routes/recipes.py - Enhanced search functionality
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.recipe import Recipe
from src.models.category import Category
from src.models.rating import Rating
from src.models.favorite import Favorite
from src.routes.auth import login_required, admin_required
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_, func, desc
import os
import uuid
import re
from src.utils.email_helper import send_rating_notification

recipes_bp = Blueprint('recipes', __name__)

# Configuration for file uploads - use absolute path relative to src directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)

        return unique_filename
    return None


@recipes_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify({
            'categories': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch categories'}), 500


@recipes_bp.route('/search', methods=['GET'])
def advanced_search():
    """Advanced recipe search with multiple filters"""
    try:
        # Get search parameters - FIXED PARAMETER NAMES
        search_query = request.args.get('q', '').strip()
        category_ids = request.args.getlist('categories[]')  # Fixed for array parameters
        min_rating = request.args.get('min_rating', type=float)
        max_cooking_time = request.args.get('max_cooking_time', type=int)
        min_cooking_time = request.args.get('min_cooking_time', type=int)
        author = request.args.get('author', '').strip()
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 12, type=int), 50)

        # Build base query for approved recipes
        query = Recipe.query.filter(Recipe.status == 'approved')

        # Text search in title, ingredients, and preparation steps
        if search_query:
            search_terms = search_query.split()
            search_conditions = []

            for term in search_terms:
                term_pattern = f"%{term}%"
                term_condition = or_(
                    Recipe.title.ilike(term_pattern),
                    Recipe.ingredients.ilike(term_pattern),
                    Recipe.preparation_steps.ilike(term_pattern)
                )
                search_conditions.append(term_condition)

            if search_conditions:
                query = query.filter(and_(*search_conditions))

        # Filter by multiple categories - IMPROVED CATEGORY FILTERING
        if category_ids and category_ids != ['']:
            try:
                # Handle both string and integer category IDs
                valid_category_ids = []
                for cat_id in category_ids:
                    if cat_id and str(cat_id).isdigit():
                        valid_category_ids.append(int(cat_id))

                if valid_category_ids:
                    query = query.filter(Recipe.category_id.in_(valid_category_ids))
            except ValueError as e:
                print(f"Category filter error: {e}")
                # Continue without category filter if there's an error

        # Filter by cooking time range
        if min_cooking_time and min_cooking_time > 0:
            query = query.filter(Recipe.cooking_time >= min_cooking_time)
        if max_cooking_time and max_cooking_time > 0:
            query = query.filter(Recipe.cooking_time <= max_cooking_time)

        # Filter by author
        if author:
            author_users = User.query.filter(User.username.ilike(f"%{author}%")).all()
            author_ids = [user.id for user in author_users]
            if author_ids:
                query = query.filter(Recipe.user_id.in_(author_ids))

        # Filter by minimum rating
        if min_rating and min_rating > 0:
            rating_subquery = db.session.query(
                Rating.recipe_id,
                func.avg(Rating.rating).label('avg_rating')
            ).group_by(Rating.recipe_id).having(func.avg(Rating.rating) >= min_rating).subquery()

            query = query.join(rating_subquery, Recipe.id == rating_subquery.c.recipe_id)

        # Sorting - IMPROVED SORTING LOGIC
        if sort_by == 'rating':
            rating_subquery = db.session.query(
                Rating.recipe_id,
                func.avg(Rating.rating).label('avg_rating')
            ).group_by(Rating.recipe_id).subquery()

            query = query.outerjoin(rating_subquery, Recipe.id == rating_subquery.c.recipe_id)
            sort_column = rating_subquery.c.avg_rating
        elif sort_by == 'cooking_time':
            sort_column = Recipe.cooking_time
        elif sort_by == 'title':
            sort_column = Recipe.title
        else:  # Default to created_at
            sort_column = Recipe.created_at

        # Apply sorting order
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Paginate results
        recipes_pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        # Get current user's favorites
        user_favorites = set()
        if 'user_id' in session:
            favorites = Favorite.query.filter_by(user_id=session['user_id']).all()
            user_favorites = {fav.recipe_id for fav in favorites}

        # Format results
        recipes_list = []
        for recipe in recipes_pagination.items:
            recipe_dict = recipe.to_dict()
            recipe_dict['is_favorited'] = recipe.id in user_favorites
            recipes_list.append(recipe_dict)

        return jsonify({
            'recipes': recipes_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': recipes_pagination.total,
                'pages': recipes_pagination.pages,
                'has_next': recipes_pagination.has_next,
                'has_prev': recipes_pagination.has_prev
            },
            'search_info': {
                'query': search_query,
                'total_results': recipes_pagination.total,
                'filters_applied': {
                    'categories': len(category_ids) if category_ids else 0,
                    'min_rating': min_rating is not None,
                    'cooking_time_range': min_cooking_time is not None or max_cooking_time is not None,
                    'author': bool(author)
                }
            }
        }), 200

    except Exception as e:
        print(f"Error in advanced_search: {str(e)}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500


@recipes_bp.route('/add', methods=['POST'])  # FIXED ROUTE PATH
@login_required
def add_recipe():
    """Add a new recipe"""
    try:
        # Get form data
        title = request.form.get('title', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        preparation_steps = request.form.get('preparation_steps', '').strip()
        category_id = request.form.get('category_id')
        cooking_time = request.form.get('cooking_time')

        # Validate required fields
        if not all([title, ingredients, preparation_steps, category_id, cooking_time]):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate category
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Invalid category'}), 400

        # Validate cooking time
        try:
            cooking_time = int(cooking_time)
            if cooking_time <= 0:
                raise ValueError
        except ValueError:
            return jsonify({'error': 'Cooking time must be a positive number'}), 400

        # Handle image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_filename = save_uploaded_file(file)
                if not image_filename:
                    return jsonify({'error': 'Invalid image file'}), 400

        # Create recipe
        recipe = Recipe(
            title=title,
            ingredients=ingredients,
            preparation_steps=preparation_steps,
            category_id=category_id,
            cooking_time=cooking_time,
            image_filename=image_filename,
            user_id=session['user_id']
        )

        db.session.add(recipe)
        db.session.commit()

        return jsonify({
            'message': 'Recipe added successfully',
            'recipe': recipe.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Add recipe error: {str(e)}")  # Debug logging
        return jsonify({'error': 'Failed to add recipe'}), 500


@recipes_bp.route('/list', methods=['GET'])
def list_recipes():
    """List recipes with optional filtering"""
    try:
        # Get query parameters
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '').strip()
        max_cooking_time = request.args.get('max_cooking_time', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'

        # Build query
        query = Recipe.query

        # Filter by approval status (default to approved only for public view)
        if approved_only:
            query = query.filter(Recipe.status == 'approved')

        # Filter by category
        if category_id:
            query = query.filter(Recipe.category_id == category_id)

        # Filter by search term (title or ingredients)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Recipe.title.ilike(search_term)) |
                (Recipe.ingredients.ilike(search_term))
            )

        # Filter by cooking time
        if max_cooking_time:
            query = query.filter(Recipe.cooking_time <= max_cooking_time)

        # Order by creation date (newest first)
        query = query.order_by(Recipe.created_at.desc())

        # Paginate
        recipes = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Get current user's favorites if logged in
        user_favorites = set()
        if 'user_id' in session:
            favorites = Favorite.query.filter_by(user_id=session['user_id']).all()
            user_favorites = {fav.recipe_id for fav in favorites}

        # Add is_favorited flag to each recipe
        recipe_list = []
        for recipe in recipes.items:
            recipe_dict = recipe.to_dict()
            recipe_dict['is_favorited'] = recipe.id in user_favorites
            recipe_list.append(recipe_dict)

        return jsonify({
            'recipes': recipe_list,
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
        print(f"Error in list_recipes: {e}")  # Debug log
        return jsonify({'error': 'Failed to fetch recipes'}), 500


@recipes_bp.route('/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    """Get a specific recipe"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)

        # Check if recipe is approved or user is the owner
        current_user_id = session.get('user_id', 0)
        if recipe.status != 'approved' and recipe.user_id != current_user_id:
            return jsonify({'error': 'Recipe not available'}), 403

        recipe_dict = recipe.to_dict()

        # Add favorite status and user's rating if user is logged in
        if current_user_id:
            favorite = Favorite.query.filter_by(
                user_id=current_user_id,
                recipe_id=recipe_id
            ).first()
            recipe_dict['is_favorited'] = favorite is not None
            
            # Check if user has rated this recipe
            user_rating = Rating.query.filter_by(
                user_id=current_user_id,
                recipe_id=recipe_id
            ).first()
            recipe_dict['user_rating'] = user_rating.to_dict() if user_rating else None
        else:
            recipe_dict['is_favorited'] = False
            recipe_dict['user_rating'] = None

        return jsonify({'recipe': recipe_dict}), 200

    except Exception as e:
        print(f"Error in get_recipe: {e}")  # Debug log
        return jsonify({'error': 'Recipe not found'}), 404


@recipes_bp.route('/<int:recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Update a recipe (only by owner)"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)

        if recipe.user_id != session['user_id']:
            return jsonify({'error': 'You can only edit your own recipes'}), 403

        # Get form data
        title = request.form.get('title', recipe.title).strip()
        ingredients = request.form.get('ingredients', recipe.ingredients).strip()
        preparation_steps = request.form.get('preparation_steps', recipe.preparation_steps).strip()
        category_id = request.form.get('category_id', recipe.category_id)
        cooking_time = request.form.get('cooking_time', recipe.cooking_time)

        # Validate required fields
        if not all([title, ingredients, preparation_steps, category_id, cooking_time]):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate category
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Invalid category'}), 400

        # Validate cooking time
        try:
            cooking_time = int(cooking_time)
            if cooking_time <= 0:
                raise ValueError
        except ValueError:
            return jsonify({'error': 'Cooking time must be a positive number'}), 400

        # Update fields
        recipe.title = title
        recipe.ingredients = ingredients
        recipe.preparation_steps = preparation_steps
        recipe.category_id = category_id
        recipe.cooking_time = cooking_time

        # Handle image upload if provided
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                image_filename = save_uploaded_file(file)
                if image_filename:
                    # Delete old image if exists
                    if recipe.image_filename:
                        old_path = os.path.join(UPLOAD_FOLDER, recipe.image_filename)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    recipe.image_filename = image_filename

        # Reset approval status when recipe is edited
        recipe.status = 'pending'

        db.session.commit()

        return jsonify({
            'message': 'Recipe updated successfully',
            'recipe': recipe.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update recipe'}), 500


@recipes_bp.route('/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe (only by owner or admin)"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        current_user = User.query.get(session['user_id'])

        # Check permissions: owner or admin
        if recipe.user_id != session['user_id'] and not current_user.is_admin():
            return jsonify({'error': 'You can only delete your own recipes'}), 403

        # Delete image file if exists
        if recipe.image_filename:
            image_path = os.path.join(UPLOAD_FOLDER, recipe.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)

        # Delete recipe (cascade will handle ratings and favorites)
        db.session.delete(recipe)
        db.session.commit()

        return jsonify({'message': 'Recipe deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete recipe'}), 500


@recipes_bp.route('/<int:recipe_id>/rate', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    """Rate a recipe"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)
        if recipe.user_id == session['user_id']:
            return jsonify({'error': 'You cannot rate your own recipe'}), 403
        
        data = request.get_json()

        rating_value = data.get('rating')
        comment = data.get('comment', '').strip()

        # Validate rating
        if not rating_value or rating_value not in [1, 2, 3, 4, 5]:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400

        # Check if user already rated this recipe
        existing_rating = Rating.query.filter_by(
            user_id=session['user_id'],
            recipe_id=recipe_id
        ).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_value
            existing_rating.comment = comment
            is_new_rating = False
        else:
            # Create new rating
            rating = Rating(
                user_id=session['user_id'],
                recipe_id=recipe_id,
                rating=rating_value,
                comment=comment
            )
            db.session.add(rating)
            is_new_rating = True

        db.session.commit()

        # Send email notification to recipe author for new ratings only
        if is_new_rating and recipe.author and recipe.author.email:
            current_user = User.query.get(session['user_id'])
            try:
                send_rating_notification(
                    author_email=recipe.author.email,
                    author_name=recipe.author.username,
                    recipe_title=recipe.title,
                    rating_value=rating_value,
                    reviewer_name=current_user.username if current_user else 'A user'
                )
            except Exception as email_error:
                print(f"Failed to send rating notification email: {email_error}")

        return jsonify({
            'message': 'Rating submitted successfully',
            'average_rating': recipe.get_average_rating(),
            'rating_count': recipe.get_rating_count()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to submit rating'}), 500


@recipes_bp.route('/<int:recipe_id>/rate', methods=['DELETE'])
@login_required
def delete_rating(recipe_id):
    """Delete user's own rating for a recipe"""
    try:
        # Find user's rating for this recipe
        rating = Rating.query.filter_by(
            user_id=session['user_id'],
            recipe_id=recipe_id
        ).first()

        if not rating:
            return jsonify({'error': 'Rating not found'}), 404

        recipe = Recipe.query.get_or_404(recipe_id)
        
        db.session.delete(rating)
        db.session.commit()

        return jsonify({
            'message': 'Rating deleted successfully',
            'average_rating': recipe.get_average_rating(),
            'rating_count': recipe.get_rating_count()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete rating'}), 500

@recipes_bp.route('/<int:recipe_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(recipe_id):
    """Toggle favorite status for a recipe"""
    try:
        recipe = Recipe.query.get_or_404(recipe_id)

        # Check if already favorited
        favorite = Favorite.query.filter_by(
            user_id=session['user_id'],
            recipe_id=recipe_id
        ).first()

        if favorite:
            # Remove from favorites
            db.session.delete(favorite)
            is_favorited = False
            message = 'Recipe removed from favorites'
        else:
            # Add to favorites
            favorite = Favorite(
                user_id=session['user_id'],
                recipe_id=recipe_id
            )
            db.session.add(favorite)
            is_favorited = True
            message = 'Recipe added to favorites'

        db.session.commit()

        return jsonify({
            'message': message,
            'is_favorited': is_favorited
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update favorite status'}), 500


@recipes_bp.route('/my-recipes', methods=['GET'])
@login_required
def get_my_recipes():
    """Get current user's recipes"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)

        recipes = Recipe.query.filter_by(user_id=session['user_id']) \
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
        print(f"Error in get_my_recipes: {e}")
        return jsonify({'error': 'Failed to fetch recipes'}), 500


@recipes_bp.route('/favorites', methods=['GET'])
@login_required
def get_favorites():
    """Get current user's favorite recipes"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)

        # Get favorite recipe IDs
        favorite_ids = db.session.query(Favorite.recipe_id) \
            .filter_by(user_id=session['user_id']) \
            .subquery()

        recipes = Recipe.query.filter(Recipe.id.in_(favorite_ids)) \
            .filter(Recipe.status == 'approved') \
            .order_by(Recipe.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        # Add is_favorited flag (all are favorites in this context)
        recipe_list = []
        for recipe in recipes.items:
            recipe_dict = recipe.to_dict()
            recipe_dict['is_favorited'] = True
            recipe_list.append(recipe_dict)

        return jsonify({
            'recipes': recipe_list,
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
        print(f"Error in get_favorites: {e}")
        return jsonify({'error': 'Failed to fetch favorite recipes'}), 500