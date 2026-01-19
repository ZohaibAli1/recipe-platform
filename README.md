# Recipe Platform

A complete recipe sharing platform built with Flask backend and SQLite database, featuring user authentication, recipe management, admin dashboard, and interactive user features.

## Features

### User Features
- **User Authentication**: Secure login/register system with role-based access (User/Admin)
- **Recipe Management**: Add, edit, and browse recipes with image uploads
- **Recipe Categories**: Vegetarian, Vegan, Non-Vegetarian, Desserts, Snacks, Beverages, Breakfast, Main Course
- **Search & Filter**: Search by recipe name, ingredients, category, and cooking time
- **Rating System**: 5-star rating system with comments
- **Favorites**: Mark recipes as favorites for easy access
- **User Dashboard**: Manage personal recipes and view favorites

### Admin Features
- **Admin Dashboard**: Overview statistics and content management
- **Recipe Moderation**: Review and approve/reject submitted recipes
- **Content Management**: Delete inappropriate content
- **User Management**: View all users and manage roles
- **Category Management**: Add/remove recipe categories

### Technical Features
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, professional interface with smooth animations
- **Image Upload**: Support for recipe images with secure file handling
- **Database**: SQLite with proper relationships and constraints
- **Security**: Password hashing, session management, input validation
- **CORS Support**: Cross-origin requests enabled for API access

## Project Structure

```
recipe-platform/
├── src/
│   ├── main.py                 # Main Flask application
│   ├── models/                 # Database models
│   │   ├── user.py            # User model with authentication
│   │   ├── recipe.py          # Recipe model
│   │   ├── category.py        # Category model
│   │   ├── rating.py          # Rating model
│   │   └── favorite.py        # Favorite model
│   ├── routes/                 # API routes
│   │   ├── auth.py            # Authentication routes
│   │   ├── recipes.py         # Recipe management routes
│   │   ├── admin.py           # Admin dashboard routes
│   │   └── user.py            # User management routes
│   ├── static/                 # Frontend files
│   │   ├── index.html         # Main HTML file
│   │   ├── app.js             # JavaScript functionality
│   │   ├── favicon.ico        # Site icon
│   │   └── uploads/           # Recipe images directory
│   └── database/
│       └── app.db             # SQLite database
├── requirements.txt            # Python dependencies
├── todo.md                    # Development progress tracker
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Extract the project**:
   ```bash
   unzip recipe-platform.zip
   cd recipe-platform
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python src/main.py
   ```

6. **Access the application**:
   Open your web browser and go to: `http://localhost:5000`

## Usage Guide

### Getting Started

1. **Register an Account**:
   - Click "Register" in the top navigation
   - Choose "User" role for regular access or "Admin" for administrative privileges
   - Fill in username, email, and password

2. **Browse Recipes**:
   - View recipe categories on the homepage
   - Use the search functionality to find specific recipes
   - Filter by category, cooking time, or search terms

3. **Add Recipes** (Logged-in users):
   - Click "Add Recipe" in the navigation
   - Fill in recipe details: title, category, cooking time, ingredients, steps
   - Optionally upload a recipe image
   - Submit for admin approval

### User Features

- **My Dashboard**: Access your personal recipes and favorites
- **Rate Recipes**: Give 1-5 star ratings with optional comments
- **Favorite Recipes**: Mark recipes as favorites for quick access
- **Edit Recipes**: Modify your own submitted recipes

### Admin Features

- **Admin Dashboard**: View platform statistics
- **Pending Recipes**: Review and approve/reject submitted recipes
- **User Management**: View all users and manage roles
- **Content Moderation**: Delete inappropriate content

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info
- `GET /api/auth/check-auth` - Check authentication status

### Recipes
- `GET /api/recipes/categories` - Get all categories
- `POST /api/recipes/add` - Add new recipe
- `GET /api/recipes/list` - List recipes with filters
- `GET /api/recipes/<id>` - Get specific recipe
- `PUT /api/recipes/<id>/edit` - Edit recipe
- `POST /api/recipes/<id>/rate` - Rate recipe
- `POST /api/recipes/<id>/favorite` - Toggle favorite
- `GET /api/recipes/my-recipes` - Get user's recipes
- `GET /api/recipes/favorites` - Get user's favorites

### Admin
- `GET /api/admin/dashboard` - Admin dashboard stats
- `GET /api/admin/recipes/pending` - Pending recipes
- `POST /api/admin/recipes/<id>/approve` - Approve recipe
- `POST /api/admin/recipes/<id>/reject` - Reject recipe
- `DELETE /api/admin/recipes/<id>/delete` - Delete recipe
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users/<id>/toggle-role` - Toggle user role

## Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `password_hash`
- `role` (user/admin)
- `created_at`

### Recipes Table
- `id` (Primary Key)
- `title`
- `ingredients` (Text)
- `preparation_steps` (Text)
- `category_id` (Foreign Key)
- `cooking_time` (Integer, minutes)
- `image_filename`
- `user_id` (Foreign Key)
- `is_approved` (Boolean)
- `created_at`
- `updated_at`

### Categories Table
- `id` (Primary Key)
- `name` (Unique)
- `description`

### Ratings Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `recipe_id` (Foreign Key)
- `rating` (1-5)
- `comment`
- `created_at`
- `updated_at`

### Favorites Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `recipe_id` (Foreign Key)
- `created_at`

## Security Features

- **Password Hashing**: Uses Werkzeug's secure password hashing
- **Session Management**: Flask sessions for user authentication
- **Input Validation**: Server-side validation for all inputs
- **File Upload Security**: Secure filename handling and file type validation
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS Configuration**: Proper cross-origin request handling

## Development Notes

- The application uses SQLite for simplicity and portability
- Default categories are automatically created on first run
- Recipe images are stored in `src/static/uploads/`
- The frontend is a single-page application with vanilla JavaScript
- All API responses are in JSON format
- Error handling is implemented throughout the application

## Troubleshooting

### Common Issues

1. **Port already in use**:
   - Change the port in `src/main.py` line: `app.run(host='0.0.0.0', port=5000, debug=True)`

2. **Database errors**:
   - Delete `src/database/app.db` and restart the application to recreate the database

3. **Image upload issues**:
   - Ensure the `src/static/uploads/` directory exists and has write permissions

4. **Virtual environment issues**:
   - Make sure the virtual environment is activated before running the application

## Future Enhancements

- Email verification for user registration
- Password reset functionality
- Recipe sharing via social media
- Advanced search with multiple filters
- Recipe collections/cookbooks
- Nutritional information
- Recipe difficulty levels
- User profiles with bio and avatar
- Recipe comments and discussions
- Mobile app development

## License

This project is created for educational purposes. Feel free to modify and use as needed.

## Support

For any issues or questions, please refer to the code comments or create an issue in the project repository.

