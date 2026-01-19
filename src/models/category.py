from src.models.user import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    recipes = db.relationship('Recipe', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'recipe_count': len(self.recipes)
        }

    @staticmethod
    def create_default_categories():
        """Create default recipe categories"""
        default_categories = [
            {'name': 'Vegetarian', 'description': 'Recipes without meat or fish'},
            {'name': 'Vegan', 'description': 'Plant-based recipes without any animal products'},
            {'name': 'Non-Vegetarian', 'description': 'Recipes containing meat, poultry, or seafood'},
            {'name': 'Desserts', 'description': 'Sweet treats and dessert recipes'},
            {'name': 'Snacks', 'description': 'Quick bites and snack recipes'},
            {'name': 'Beverages', 'description': 'Drink recipes and beverages'},
            {'name': 'Breakfast', 'description': 'Morning meal recipes'},
            {'name': 'Main Course', 'description': 'Primary meal dishes'}
        ]
        
        for cat_data in default_categories:
            existing = Category.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = Category(name=cat_data['name'], description=cat_data['description'])
                db.session.add(category)
        
        db.session.commit()

