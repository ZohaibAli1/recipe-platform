# src/models/recipe.py
# Changes: Standardize Rating to use 'rating' instead of 'score'
# Update get_average_rating to use 'rating'
# Remove duplicate Category, Rating, Favorite definitions (use separate files)
# Keep only Recipe and necessary methods
from datetime import datetime
from src.models.user import db

class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    preparation_steps = db.Column(db.Text, nullable=False)
    cooking_time = db.Column(db.Integer, nullable=False)  # in minutes
    image_filename = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    # Relationships
    ratings = db.relationship('Rating', backref='recipe', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='recipe', lazy=True, cascade='all, delete-orphan')

    def get_average_rating(self):
        if not self.ratings:
            return 0
        return sum(rating.rating for rating in self.ratings) / len(self.ratings)

    def get_rating_count(self):
        return len(self.ratings)

    def is_favorited_by(self, user_id):
        return any(fav.user_id == user_id for fav in self.favorites)

    def __repr__(self):
        return f'<Recipe {self.title}>'

    def to_dict(self, include_author=True):
        recipe_dict = {
            'id': self.id,
            'title': self.title,
            'ingredients': self.ingredients,
            'preparation_steps': self.preparation_steps,
            'cooking_time': self.cooking_time,
            'image_filename': self.image_filename,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'category': self.category.to_dict() if self.category else None,
            'average_rating': round(self.get_average_rating(), 1),
            'rating_count': self.get_rating_count()
        }

        if include_author and self.author:
            recipe_dict['author'] = {
                'id': self.author.id,
                'username': self.author.username
            }

        return recipe_dict