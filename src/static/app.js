// static/app.js
// Global state
let currentUser = null;
let currentRecipes = [];
let currentCategories = [];
let imageErrorHandled = new WeakMap(); // Track images that errored to prevent infinite loops

// Initialize app
document.addEventListener('DOMContentLoaded', function () {
    checkAuthStatus();
    loadCategories();
    loadRecipes();
    setupEventListeners();
    checkResetToken(); // Check if there's a reset token in URL
});

// Setup event listeners
function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Register form
    document.getElementById('register-form').addEventListener('submit', handleRegister);

    // Add recipe form
    document.getElementById('add-recipe-form').addEventListener('submit', handleAddRecipe);

    // Search form (home)
    document.getElementById('search-form').addEventListener('submit', handleSearch);

    // Browse search form (recipes section)
    if (document.getElementById('browse-search-form')) {
        document.getElementById('browse-search-form').addEventListener('submit', handleBrowseSearch);
    }

    // Password reset forms
    document.getElementById('forgot-password-form').addEventListener('submit', handleForgotPassword);
    document.getElementById('reset-password-form').addEventListener('submit', handleResetPassword);


    // Close modals when clicking outside
    window.addEventListener('click', function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    });
}

// Authentication functions
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/check-auth');
        const data = await response.json();
        if (data.authenticated) {
            currentUser = data.user;
            updateUIForLoggedInUser();
        } else {
            updateUIForGuest();
        }
    } catch (error) {
        updateUIForGuest();
    }
}

function updateUIForLoggedInUser() {
    document.getElementById('auth-buttons-guest').classList.add('hidden');
    document.getElementById('auth-buttons-user').classList.remove('hidden');
    document.getElementById('user-welcome').textContent = `Welcome, ${currentUser.username}`;
    document.getElementById('add-recipe-link').classList.remove('hidden');
    document.getElementById('dashboard-link').classList.remove('hidden');
    if (currentUser.role === 'admin') {
        document.getElementById('admin-link').classList.remove('hidden');
    }
}

function updateUIForGuest() {
    document.getElementById('auth-buttons-guest').classList.remove('hidden');
    document.getElementById('auth-buttons-user').classList.add('hidden');
    document.getElementById('add-recipe-link').classList.add('hidden');
    document.getElementById('dashboard-link').classList.add('hidden');
    document.getElementById('admin-link').classList.add('hidden');
}

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
        const data = await response.json();
        if (response.ok) {
            currentUser = data.user;
            updateUIForLoggedInUser();
            closeModal('login-modal');
            showSuccess('Login successful!');
            document.getElementById('login-form').reset();
            loadRecipes();
        } else {
            showError(data.error || 'Login failed');
        }
    } catch (error) {
        showError('Login failed. Please try again.');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const role = document.getElementById('register-role').value;
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, role }),
        });
        const data = await response.json();
        if (response.ok) {
            currentUser = data.user;
            updateUIForLoggedInUser();
            closeModal('register-modal');
            showSuccess('Registration successful!');
            document.getElementById('register-form').reset();
            loadRecipes();
        } else {
            showError(data.error || 'Registration failed');
        }
    } catch (error) {
        showError('Registration failed. Please try again.');
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
        currentUser = null;
        updateUIForGuest();
        showHome();
        showSuccess('Logged out successfully!');
        loadRecipes();
    } catch (error) {
        showError('Logout failed');
    }
}

// Category functions
async function loadCategories() {
    try {
        const response = await fetch('/api/recipes/categories');
        const data = await response.json();
        if (response.ok) {
            currentCategories = data.categories;
            displayCategories();
            populateCategoryFilters();
        } else {
            showError('Failed to load categories');
        }
    } catch (error) {
        showError('Failed to load categories');
    }
}

function populateCategoryFilters() {
    const selects = [
        document.getElementById('category-filter'),
        document.getElementById('browse-category'),
        document.getElementById('recipe-category')
    ];
    selects.forEach(select => {
        if (select) {
            select.innerHTML = '<option value="">' + (select.id === 'recipe-category' ? 'Select Category' : 'All Categories') + '</option>';
            currentCategories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                select.appendChild(option);
            });
        }
    });
}

function displayCategories() {
    const grid = document.getElementById('categories-grid');
    if (grid) {
        grid.innerHTML = currentCategories.map(category => `
            <div class="category-card" onclick="filterByCategory(${category.id})">
                <h4>${category.name}</h4>
                <p>${category.description || 'No description'}</p>
                <p>${category.recipe_count || 0} recipes</p>
            </div>
        `).join('');
    }
}

// Recipe functions
async function loadRecipes(params = {}) {
    try {
        const url = new URL('/api/recipes/search', window.location.origin);

        // Properly handle array parameters (categories)
        Object.keys(params).forEach(key => {
            if (params[key] !== undefined && params[key] !== '' && params[key] !== null) {
                if (Array.isArray(params[key])) {
                    params[key].forEach(value => {
                        if (value) url.searchParams.append(key + '[]', value);
                    });
                } else {
                    url.searchParams.append(key, params[key]);
                }
            }
        });

        const response = await fetch(url);

        const data = await response.json();
        if (response.ok) {
            currentRecipes = data.recipes;
            displayRecipes();
        } else {
            showError(data.error || 'Failed to load recipes');
        }
    } catch (error) {
        showError('Failed to load recipes: ' + error.message);
    }
}

function displayRecipes() {
    const grid = document.getElementById('recipes-grid');
    if (grid) {
        grid.innerHTML = currentRecipes.map(recipe => {
            const imageElement = recipe.image_filename ?
                `<img src="/static/uploads/${recipe.image_filename}" alt="${recipe.title}"
                      onerror="handleImageError(this, '${recipe.title}')" loading="lazy">` :
                `<div class="no-image-placeholder">No Image</div>`;
            return `
                <div class="recipe-card" onclick="showRecipeDetail(${recipe.id})">
                    <div class="recipe-image">
                        ${imageElement}
                    </div>
                    <h4>${recipe.title}</h4>
                    <div class="recipe-meta">
                        <span>${recipe.cooking_time} min</span>
                        <span class="recipe-rating">★ ${recipe.average_rating || 0} (${recipe.rating_count || 0})</span>
                    </div>
                </div>
            `;
        }).join('');
    }
}

// Search handlers
async function handleSearch(event) {
    event.preventDefault();

    const categorySelect = document.getElementById('category-filter');
    const categories = Array.from(categorySelect.selectedOptions)
        .map(opt => opt.value)
        .filter(v => v && v !== '');

    const params = {
        q: document.getElementById('search-query').value,
        categories: categories,
        min_cooking_time: document.getElementById('min-cooking-time').value || null,
        max_cooking_time: document.getElementById('max-cooking-time').value || null,
        min_rating: document.getElementById('min-rating-filter').value || null,
        author: document.getElementById('author-filter').value || null,
        sort_by: document.getElementById('sort-by').value,
        sort_order: document.getElementById('sort-by').value === 'cooking_time' ? 'asc' : 'desc'
    };

    await loadRecipes(params);
    showRecipes();
}

async function handleBrowseSearch(event) {
    event.preventDefault();

    const categorySelect = document.getElementById('browse-category');
    const categories = Array.from(categorySelect.selectedOptions)
        .map(opt => opt.value)
        .filter(v => v && v !== '');

    const params = {
        categories: categories,
        max_cooking_time: document.getElementById('browse-max-cooking-time').value || null,
        sort_by: document.getElementById('browse-sort-by').value,
        sort_order: document.getElementById('browse-sort-by').value === 'cooking_time' ? 'asc' : 'desc'
    };

    await loadRecipes(params);
}

function quickFilter(type) {
    let params = {};
    switch (type) {
        case 'quick':
            params.max_cooking_time = 30;
            break;
        case 'high_rated':
            params.min_rating = 4;
            break;
        case 'vegetarian':
            params.categories = currentCategories
                .filter(cat => cat.name.toLowerCase().includes('vegetarian'))
                .map(cat => cat.id);
            break;
        case 'vegan':
            params.categories = currentCategories
                .filter(cat => cat.name.toLowerCase().includes('vegan'))
                .map(cat => cat.id);
            break;
    }
    loadRecipes(params);
    showRecipes();
}

function clearFilters() {
    document.getElementById('search-form').reset();
    loadRecipes();
}

function showTrending() {
    loadRecipes({ sort_by: 'rating', sort_order: 'desc' });
    showRecipes();
}

async function handleAddRecipe(event) {
    event.preventDefault();
    const formData = new FormData();
    formData.append('title', document.getElementById('recipe-title').value);
    formData.append('category_id', document.getElementById('recipe-category').value);
    formData.append('ingredients', document.getElementById('recipe-ingredients').value);
    formData.append('preparation_steps', document.getElementById('recipe-steps').value);
    formData.append('cooking_time', document.getElementById('recipe-cooking-time').value);
    const file = document.getElementById('recipe-image').files[0];
    if (file) {
        formData.append('image', file);
    }
    try {
        const response = await fetch('/api/recipes/add', {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        if (response.ok) {
            closeModal('add-recipe-modal');
            showSuccess('Recipe added successfully!');
            document.getElementById('add-recipe-form').reset();
            loadRecipes();
        } else {
            showError(data.error || 'Failed to add recipe');
        }
    } catch (error) {
        showError('Failed to add recipe');
    }
}

async function showRecipeDetail(recipeId) {
    try {
        const response = await fetch(`/api/recipes/${recipeId}`);
        const data = await response.json();
        if (response.ok) {
            const recipe = data.recipe;
            document.getElementById('recipe-detail-title').textContent = recipe.title;
            const image = document.getElementById('recipe-detail-image');
            if (recipe.image_filename) {
                image.src = `/static/uploads/${recipe.image_filename}`;
                image.alt = recipe.title;
                image.style.display = 'block';
            } else {
                image.style.display = 'none';
            }
            document.getElementById('recipe-detail-category').textContent = `Category: ${recipe.category.name}`;
            document.getElementById('recipe-detail-cooking-time').textContent = `Cooking Time: ${recipe.cooking_time} minutes`;
            document.getElementById('recipe-detail-rating').textContent = `Rating: ⭐ ${recipe.average_rating || 0} (${recipe.rating_count || 0} ratings)`;
            document.getElementById('recipe-detail-author').textContent = `Author: ${recipe.author ? recipe.author.username : 'Unknown'}`;
            document.getElementById('recipe-detail-ingredients').textContent = recipe.ingredients;
            document.getElementById('recipe-detail-steps').textContent = recipe.preparation_steps;
            document.getElementById('recipe-detail-modal').style.display = 'flex';

            // Add actions if logged in
            const content = document.querySelector('#recipe-detail-modal .recipe-content');
            content.querySelectorAll('.recipe-actions').forEach(el => el.remove()); // Remove existing actions
            if (currentUser) {
                const isOwnRecipe = recipe.user_id === currentUser.id;
                const hasRated = recipe.user_rating !== null;

                const actions = document.createElement('div');
                actions.className = 'recipe-actions';

                let ratingButtons = '';
                if (!isOwnRecipe) {
                    if (hasRated) {
                        ratingButtons = `
                            <button class="btn btn-primary" onclick="rateRecipe(${recipe.id})">Update Rating (${recipe.user_rating.rating}★)</button>
                            <button class="btn btn-secondary" onclick="deleteRating(${recipe.id})">Delete Rating</button>
                        `;
                    } else {
                        ratingButtons = `<button class="btn btn-primary" onclick="rateRecipe(${recipe.id})">Rate</button>`;
                    }
                }

                actions.innerHTML = `
                    ${ratingButtons}
                    <button class="btn btn-primary" onclick="toggleFavorite(${recipe.id})">${recipe.is_favorited ? 'Remove Favorite' : 'Add Favorite'}</button>
                    ${isOwnRecipe || currentUser.role === 'admin' ? `
                        <button class="btn btn-primary" onclick="editRecipe(${recipe.id})">Edit</button>
                        <button class="btn btn-secondary" onclick="deleteRecipe(${recipe.id})">Delete</button>
                    ` : ''}
                `;
                content.appendChild(actions);
            }
        } else {
            showError('Failed to load recipe detail');
        }
    } catch (error) {
        showError('Failed to load recipe detail');
    }
}

function handleImageError(img, title) {
    if (!imageErrorHandled.has(img)) {
        imageErrorHandled.set(img, true);
        img.src = '';
        img.alt = 'Image not available';
        img.parentElement.innerHTML = '<div class="no-image-placeholder">No Image</div>';
    }
}

async function toggleFavorite(recipeId) {
    try {
        const response = await fetch(`/api/recipes/${recipeId}/favorite`, {
            method: 'POST',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess(data.message);
            loadRecipes();
            closeModal('recipe-detail-modal');
        } else {
            showError(data.error || 'Failed to update favorite');
        }
    } catch (error) {
        showError('Failed to update favorite');
    }
}

async function rateRecipe(recipeId) {
    const rating = prompt('Enter rating (1-5):');
    const comment = prompt('Enter comment (optional):');
    if (rating) {
        try {
            const response = await fetch(`/api/recipes/${recipeId}/rate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rating: parseInt(rating), comment }),
            });
            const data = await response.json();
            if (response.ok) {
                showSuccess('Rating submitted!');
                closeModal('recipe-detail-modal');
                loadRecipes();
            } else if (response.status === 403) {
                showError(data.error || 'You cannot rate your own recipe');
            } else {
                showError(data.error || 'Failed to submit rating');
            }
        } catch (error) {
            showError('Failed to submit rating');
        }
    }
}

async function deleteRating(recipeId) {
    if (!confirm('Are you sure you want to delete your rating?')) {
        return;
    }
    try {
        const response = await fetch(`/api/recipes/${recipeId}/rate`, {
            method: 'DELETE',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess('Rating deleted successfully!');
            closeModal('recipe-detail-modal');
            loadRecipes();
        } else {
            showError(data.error || 'Failed to delete rating');
        }
    } catch (error) {
        showError('Failed to delete rating');
    }
}

async function deleteRecipe(recipeId) {
    if (!confirm('Are you sure you want to delete this recipe?')) {
        return;
    }
    try {
        const response = await fetch(`/api/recipes/${recipeId}`, {
            method: 'DELETE',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess('Recipe deleted successfully!');
            closeModal('recipe-detail-modal');
            loadRecipes();
            if (document.getElementById('dashboard-content').offsetParent !== null) {
                showMyRecipes();
            } else if (document.getElementById('admin-content').offsetParent !== null) {
                showPendingRecipes();
                loadAdminStats();
            }
        } else {
            showError(data.error || 'Failed to delete recipe');
        }
    } catch (error) {
        showError('Failed to delete recipe');
    }
}

function editRecipe(recipeId) {
    // Placeholder for edit functionality
    alert('Edit functionality to be implemented');
    // To implement: Fetch recipe, populate a form similar to add-recipe, submit PUT to /api/recipes/<id>
}

function filterByCategory(id) {
    loadRecipes({ categories: [id] });
    showRecipes();
}

function showDashboard() {
    hideAllSections();
    document.getElementById('dashboard-section').classList.remove('hidden');
    showMyRecipes();
}

async function showMyRecipes() {
    try {
        const response = await fetch('/api/recipes/my-recipes');
        const data = await response.json();
        if (response.ok) {
            const content = document.getElementById('dashboard-content');
            content.innerHTML = `
                <h3>My Recipes</h3>
                <div class="dashboard-recipes-grid">
                    ${data.recipes.map(recipe => `
                        <div class="recipe-card" onclick="showRecipeDetail(${recipe.id})">
                            <div class="recipe-image">
                                ${recipe.image_filename ?
                    `<img src="/static/uploads/${recipe.image_filename}" alt="${recipe.title}"
                                          onerror="handleImageError(this, '${recipe.title}')" loading="lazy">` :
                    '<div class="no-image-placeholder">No Image</div>'
                }
                            </div>
                            <h4>${recipe.title}</h4>
                            <div class="recipe-meta">
                                <span>${recipe.cooking_time} min</span>
                                <span class="recipe-status status-${recipe.status}">${recipe.status}</span>
                            </div>
                            <div class="recipe-actions" onclick="event.stopPropagation();">
                                <button class="btn btn-primary btn-small" onclick="editRecipe(${recipe.id})">Edit</button>
                                <button class="btn btn-secondary btn-small" onclick="deleteRecipe(${recipe.id})">Delete</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showError('Failed to load my recipes');
        }
    } catch (error) {
        showError('Failed to load my recipes');
    }
}

async function showFavorites() {
    try {
        const response = await fetch('/api/recipes/favorites');
        const data = await response.json();
        if (response.ok) {
            const content = document.getElementById('dashboard-content');
            content.innerHTML = `
                <h3>Favorite Recipes</h3>
                <div class="dashboard-recipes-grid">
                    ${data.recipes.map(recipe => `
                        <div class="recipe-card" onclick="showRecipeDetail(${recipe.id})">
                            <div class="recipe-image">
                                ${recipe.image_filename ?
                    `<img src="/static/uploads/${recipe.image_filename}" alt="${recipe.title}"
                                          onerror="handleImageError(this, '${recipe.title}')" loading="lazy">` :
                    '<div class="no-image-placeholder">No Image</div>'
                }
                            </div>
                            <h4>${recipe.title}</h4>
                            <div class="recipe-meta">
                                <span>${recipe.cooking_time} min</span>
                                <span class="recipe-rating">★ ${recipe.average_rating || 0} (${recipe.rating_count || 0})</span>
                            </div>
                            <div class="recipe-actions" onclick="event.stopPropagation();">
                                <button class="btn btn-secondary btn-small" onclick="toggleFavorite(${recipe.id})">Remove Favorite</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showError('Failed to load favorites');
        }
    } catch (error) {
        showError('Failed to load favorites');
    }
}

function showAdminDashboard() {
    hideAllSections();
    document.getElementById('admin-section').classList.remove('hidden');
    loadAdminStats();
}

async function loadAdminStats() {
    try {
        const response = await fetch('/api/admin/dashboard');
        const data = await response.json();
        if (response.ok) {
            const stats = data.stats;
            const content = document.getElementById('admin-content');
            content.innerHTML = `
                <h3>Dashboard Stats</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Total Users</h4>
                        <p>${stats.total_users}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Total Recipes</h4>
                        <p>${stats.total_recipes}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Pending Recipes</h4>
                        <p>${stats.pending_recipes}</p>
                    </div>
                    <div class="stat-card">
                        <h4>Total Ratings</h4>
                        <p>${stats.total_ratings}</p>
                    </div>
                </div>
                <div class="admin-actions">
                    <button class="btn btn-primary" onclick="showPendingRecipes()">View Pending Recipes</button>
                </div>
            `;
        } else {
            showError('Failed to load admin stats');
        }
    } catch (error) {
        showError('Failed to load admin stats');
    }
}

async function showPendingRecipes() {
    try {
        const response = await fetch('/api/admin/recipes/pending');
        const data = await response.json();
        if (response.ok) {
            const content = document.getElementById('admin-content');
            content.innerHTML = `
                <h3>Pending Recipes</h3>
                <div class="admin-recipes-grid">
                    ${data.recipes.map(recipe => `
                        <div class="recipe-card admin-recipe-card" onclick="showRecipeDetail(${recipe.id})">
                            <div class="recipe-image">
                                ${recipe.image_filename ?
                    `<img src="/static/uploads/${recipe.image_filename}" alt="${recipe.title}"
                                          onerror="handleImageError(this, '${recipe.title}')" loading="lazy">` :
                    '<div class="no-image-placeholder">No Image</div>'
                }
                            </div>
                            <h4>${recipe.title}</h4>
                            <div class="recipe-meta">
                                <span>${recipe.cooking_time} min</span>
                                <span>By ${recipe.author ? recipe.author.username : 'Unknown'}</span>
                            </div>
                            <div class="recipe-actions admin-actions" onclick="event.stopPropagation();">
                                <button class="btn btn-primary btn-small" onclick="approveRecipe(${recipe.id})">Approve</button>
                                <button class="btn btn-secondary btn-small" onclick="rejectRecipe(${recipe.id})">Reject</button>
                                <button class="btn btn-danger btn-small" onclick="deleteRecipe(${recipe.id})">Delete</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showError('Failed to load pending recipes');
        }
    } catch (error) {
        showError('Failed to load pending recipes');
    }
}

async function approveRecipe(recipeId) {
    try {
        const response = await fetch(`/api/admin/recipes/${recipeId}/approve`, {
            method: 'POST',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess('Recipe approved successfully!');
            showPendingRecipes();
            loadAdminStats();
        } else {
            showError(data.error || 'Failed to approve recipe');
        }
    } catch (error) {
        showError('Failed to approve recipe');
    }
}

async function rejectRecipe(recipeId) {
    try {
        const response = await fetch(`/api/admin/recipes/${recipeId}/reject`, {
            method: 'POST',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess('Recipe rejected successfully!');
            showPendingRecipes();
            loadAdminStats();
        } else {
            showError(data.error || 'Failed to reject recipe');
        }
    } catch (error) {
        showError('Failed to reject recipe');
    }
}

async function showUsers() {
    try {
        const response = await fetch('/api/admin/users');
        const data = await response.json();
        if (response.ok) {
            displayUsers(data.users);
        } else {
            showError('Failed to load users');
        }
    } catch (error) {
        showError('Failed to load users');
    }
}

function displayUsers(users) {
    const content = document.getElementById('admin-content');
    content.innerHTML = `
        <h3>Users</h3>
        <div class="users-list">
            ${users.map(user => `
                <div class="user-card">
                    <span>${user.username}</span>
                    <span>${user.email}</span>
                    <span class="user-role">${user.role}</span>
                    <span class="user-date">${new Date(user.created_at).toLocaleDateString()}</span>
                    <div class="user-actions">
                        <button class="btn btn-primary btn-small" onclick="toggleUserRole(${user.id})">Toggle Role</button>
                        <button class="btn btn-secondary btn-small" onclick="deleteUser(${user.id})">Delete</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

async function toggleUserRole(userId) {
    try {
        const response = await fetch(`/api/admin/users/${userId}/toggle-role`, {
            method: 'POST',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess(data.message);
            showUsers();
        } else {
            showError(data.error || 'Failed to toggle role');
        }
    } catch (error) {
        showError('Failed to toggle role');
    }
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    try {
        const response = await fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
        });
        const data = await response.json();
        if (response.ok) {
            showSuccess('User deleted successfully!');
            showUsers();
            loadAdminStats();
        } else {
            showError(data.error || 'Failed to delete user');
        }
    } catch (error) {
        showError('Failed to delete user');
    }
}

async function showAdminCategories() {
    const content = document.getElementById('admin-content');
    content.innerHTML = `
        <h3>Manage Categories</h3>
        <div class="categories-management">
            <div class="category-form">
                <h4>Add New Category</h4>
                <form id="add-category-form" onsubmit="addCategory(event)">
                    <input type="text" id="category-name" placeholder="Category Name" required>
                    <textarea id="category-description" placeholder="Category Description"></textarea>
                    <button type="submit" class="btn btn-primary">Add Category</button>
                </form>
            </div>
            <div class="categories-list">
                <h4>Existing Categories</h4>
                ${currentCategories.map(category => `
                    <div class="category-item">
                        <span class="category-name">${category.name}</span>
                        <span class="category-count">${category.recipe_count} recipes</span>
                        <button class="btn btn-secondary btn-small" onclick="deleteCategory(${category.id})">Delete</button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

async function showPasswordResets() {
    try {
        const response = await fetch('/api/admin/password-resets');
        const data = await response.json();

        if (response.ok) {
            const content = document.getElementById('admin-content');
            content.innerHTML = `
                <h3>Password Reset Logs</h3>
                <p style="color: #6c757d; margin-bottom: 20px;">Recent password reset requests (showing last 50)</p>
                <div class="users-list">
                    ${data.password_resets.length > 0 ? data.password_resets.map(reset => `
                        <div class="user-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                <span style="font-weight: bold;">${reset.username}</span>
                                <span class="status-badge ${reset.status.toLowerCase()}">${reset.status}</span>
                            </div>
                            <span>${reset.email}</span>
                            ${reset.requested_at ? `<span class="user-date">Requested: ${new Date(reset.requested_at).toLocaleString()}</span>` : ''}
                            ${reset.last_reset ? `<span class="user-date">Reset: ${new Date(reset.last_reset).toLocaleString()}</span>` : ''}
                        </div>
                    `).join('') : '<p style="text-align: center; color: #6c757d;">No password resets yet</p>'}
                </div>
            `;
        } else {
            showError('Failed to load password reset logs');
        }
    } catch (error) {
        showError('Failed to load password reset logs');
    }
}


// Navigation functions
function showHome() {
    hideAllSections();
    document.getElementById('home-section').classList.remove('hidden');
}

function showRecipes() {
    hideAllSections();
    document.getElementById('recipes-section').classList.remove('hidden');
}

function showAbout() {
    hideAllSections();
    document.getElementById('about-section').classList.remove('hidden');
}

function showTerms() {
    hideAllSections();
    document.getElementById('terms-section').classList.remove('hidden');
}

function showContact() {
    hideAllSections();
    document.getElementById('contact-section').classList.remove('hidden');
}

function hideAllSections() {
    const sections = document.querySelectorAll('main > section');
    sections.forEach(section => section.classList.add('hidden'));
}

// Modal functions
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'flex';
}

function showLogin() {
    document.getElementById('login-modal').style.display = 'flex';
}

function showRegister() {
    document.getElementById('register-modal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Utility functions
function showError(message) {
    const existingAlerts = document.querySelectorAll('.error, .success');
    existingAlerts.forEach(alert => alert.remove());
    const alert = document.createElement('div');
    alert.className = 'error';
    alert.textContent = message;
    document.querySelector('main').insertBefore(alert, document.querySelector('main').firstChild);
    setTimeout(() => alert.remove(), 5000);
}

function showSuccess(message) {
    const existingAlerts = document.querySelectorAll('.error, .success');
    existingAlerts.forEach(alert => alert.remove());
    const alert = document.createElement('div');
    alert.className = 'success';
    alert.textContent = message;
    document.querySelector('main').insertBefore(alert, document.querySelector('main').firstChild);
    setTimeout(() => alert.remove(), 5000);
}

// Password Reset Functions
async function handleForgotPassword(event) {
    event.preventDefault();
    const email = document.getElementById('forgot-email').value.trim();

    if (!email) {
        showError('Please enter your email address');
        return;
    }

    try {
        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message || 'Password reset link sent! Check your email');
            document.getElementById('forgot-password-form').reset();
            closeModal('forgot-password-modal');
        } else {
            showError(data.error || 'Failed to send reset link');
        }
    } catch (error) {
        showError('Failed to process request. Please try again.');
    }
}

function checkResetToken() {
    // Check if URL has reset_token parameter
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('reset_token');

    if (resetToken) {
        // Verify token and show reset password modal
        verifyAndShowResetModal(resetToken);
        // Clean URL
        window.history.replaceState({}, document.title, window.location.pathname);
    }
}

async function verifyAndShowResetModal(token) {
    try {
        const response = await fetch('/api/auth/verify-reset-token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (response.ok && data.valid) {
            // Token is valid, show reset password modal
            document.getElementById('reset-token').value = token;
            showModal('reset-password-modal');
            showSuccess(`Welcome ${data.username}! Please enter your new password.`);
        } else {
            showError(data.error || 'Invalid or expired reset link. Please request a new one.');
            setTimeout(() => showModal('forgot-password-modal'), 2000);
        }
    } catch (error) {
        showError('Failed to verify reset link');
    }
}

async function handleResetPassword(event) {
    event.preventDefault();

    const token = document.getElementById('reset-token').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    // Validate passwords match
    if (newPassword !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }

    // Validate password strength
    if (newPassword.length < 6) {
        showError('Password must be at least 6 characters long');
        return;
    }

    if (!/[A-Za-z]/.test(newPassword)) {
        showError('Password must contain at least one letter');
        return;
    }

    if (!/[0-9]/.test(newPassword)) {
        showError('Password must contain at least one number');
        return;
    }

    try {
        const response = await fetch('/api/auth/reset-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, password: newPassword }),
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(data.message || 'Password reset successfully! You can now login.');
            document.getElementById('reset-password-form').reset();
            closeModal('reset-password-modal');
            // Show login modal after 2 seconds
            setTimeout(() => showLogin(), 2000);
        } else {
            showError(data.error || 'Failed to reset password');
        }
    } catch (error) {
        showError('Failed to reset password. Please try again.');
    }
}