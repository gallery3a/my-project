from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# Helper function to update visit count using a context manager for database connection
def update_visit_count(page_name):
    attempt = 0
    max_retries = 3
    while attempt < max_retries:
        try:
            # Using 'with' ensures the connection is properly closed after each operation
            with sqlite3.connect('database/recipes.db', timeout=10) as conn:  # Timeout in seconds
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM visits WHERE page = ?", (page_name,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("UPDATE visits SET visit_count = visit_count + 1 WHERE page = ?", (page_name,))
                else:
                    cursor.execute("INSERT INTO visits (page, visit_count) VALUES (?, ?)", (page_name, 1))
                conn.commit()  # Ensure the changes are committed
            break  # If the operation is successful, exit the loop
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < max_retries - 1:
                attempt += 1
                time.sleep(1)  # Wait before retrying
            else:
                print(f"Database error: {e}")
                break

# Route to search recipes based on query
@app.route('/search', methods=['GET'])
def search_recipes():
    query = request.args.get('query', '').lower()
    
    # Fetch recipes from the database where the name contains the search query
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE name LIKE ?", ('%' + query + '%',))
        recipes = cursor.fetchall()
    
    # Return the results as JSON
    result = []
    for recipe in recipes:
        result.append({
            'name': recipe[1],
            'description': recipe[2],
            'ingredients': recipe[3],
            'instructions': recipe[4],
        })
    
    return jsonify({"recipes": result})

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials in the database
        with sqlite3.connect('database/recipes.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()

        if user:
            # Set session variables
            session['user_id'] = user[0]  # Store user ID
            session['username'] = user[1]  # Store username
            
            # If the user is an admin, set the admin session variable
            cursor.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
            is_admin = cursor.fetchone()
            
            if is_admin and is_admin[0]:  # Check if the user is an admin
                session['admin'] = True  # Set admin session if the user is an admin
            else:
                session['admin'] = False  # Set to False for non-admins

            # Redirect based on admin status
            if username == 'admin' and password == 'adminpassword':  # Check for hardcoded admin credentials
                session['admin'] = True  # Force admin session for the hardcoded admin
                return redirect(url_for('admin_home'))  # Redirect to admin dashboard
            else:
                return redirect(url_for('homepage'))  # Redirect to homepage for normal users
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/breakfast')
def breakfast_page():
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE category_id = 1")
        recipes = cursor.fetchall()

    # Update visit count for this page
    update_visit_count('breakfast')

    return render_template('breakfast.html', recipes=recipes)

# Route for the admin dashboard
@app.route('/admin')
def admin_home():
    # Check if the user is an admin
    if not session.get('admin'):
        return redirect(url_for('login'))  # Redirect to login if not an admin

    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        # Fetch all recipes for admin view
        cursor.execute("SELECT * FROM recipes")
        recipes = cursor.fetchall()

    # Fetch visit data if needed
    cursor.execute("SELECT page, visit_count FROM visits")
    visits = cursor.fetchall()

    return render_template('admin.html', recipes=recipes, visits=visits)



# Route to log out
@app.route('/logout')
def logout():
    session.pop('admin', None)
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Route to delete a recipe
@app.route('/delete_recipe/<int:recipe_id>')
def delete_recipe(recipe_id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    # Step 1: Delete the recipe from the database
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        conn.commit()

    # Step 2: Check if there's a search query in the URL
    query = request.args.get('query', None)
    if query:
        # If there's a search query, we want to redirect back to the search results
        return redirect(url_for('search_recipes', query=query))  # Keep the search query intact
    
    # Step 3: If no search query exists, redirect back to the admin home
    return redirect(url_for('admin_home'))

# Route to add a new recipe
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if not session.get('admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category_id = request.form['category_id']  # Get the category ID from the form

        with sqlite3.connect('database/recipes.db') as conn:
            cursor = conn.cursor()
            cursor.execute(""" 
                INSERT INTO recipes (name, description, ingredients, instructions, category_id)
                VALUES (?, ?, ?, ?, ?)
            """, (name, description, ingredients, instructions, category_id))
            conn.commit()

        return redirect(url_for('admin_home'))

    return render_template('add_recipe.html')

@app.route('/<category>', methods=['GET'])
def show_category(category):
    # Map category names to category IDs
    category_map = {
        'breakfast': 1,
        'lunch': 2,
        'dinner': 3,
        'desserts': 4,
        'mazaqat': 5
    }

    # Get the category ID from the category name
    category_id = category_map.get(category.lower())
    if not category_id:
        return "Category not found", 404

    # Get the search query from the URL, if any
    query = request.args.get('query', '').lower()

    # Fetch recipes for the given category with an optional search filter
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        if query:
            cursor.execute("SELECT * FROM recipes WHERE category_id = ? AND name LIKE ?", (category_id, '%' + query + '%'))
        else:
            cursor.execute("SELECT * FROM recipes WHERE category_id = ?", (category_id,))
        recipes = cursor.fetchall()

    # Update visit count for this category page
    update_visit_count(category)

    # Render the category.html template with the recipes
    return render_template('category.html', category=category.capitalize(), recipes=recipes, query=query)

@app.route('/lunch')
def lunch():
    category = "lunch"  # Define category
    recipes = get_recipes_for_category(category)  # Fetch recipes based on category

    return render_template('lunch.html', recipes=recipes, category=category)

# Function to fetch recipes for a given category (e.g., lunch, dinner)
def get_recipes_for_category(category):
    # Assuming you want to fetch recipes based on category from the database
    category_map = {
        'breakfast': 1,
        'lunch': 2,
        'dinner': 3,
        'desserts': 4,
        'mazaqat': 5
    }
    
    category_id = category_map.get(category.lower())
    if not category_id:
        return []

    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE category_id = ?", (category_id,))
        recipes = cursor.fetchall()
    
    return recipes

@app.route('/dinner')
def dinner_page():
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE category_id = 3")  # Category ID for dinner
        recipes = cursor.fetchall()

    # Update visit count for this page
    update_visit_count('dinner')

    return render_template('dinner.html', recipes=recipes)

@app.route('/desserts')
def desserts_page():
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE category_id = 4")  # Category ID for desserts
        recipes = cursor.fetchall()

    # Update visit count for this page
    update_visit_count('desserts')

    return render_template('desserts.html', recipes=recipes)

# Route to edit a recipe
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            ingredients = request.form['ingredients']
            instructions = request.form['instructions']

            cursor.execute("""
                UPDATE recipes
                SET name = ?, description = ?, ingredients = ?, instructions = ?
                WHERE id = ?
            """, (name, description, ingredients, instructions, recipe_id))
            conn.commit()

            return redirect(url_for('admin_home'))

        cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
        recipe = cursor.fetchone()

    return render_template('edit_recipe.html', recipe=recipe)

# Route to view visit counts
@app.route('/visit_counts')
def visit_counts():
    if not session.get('admin'):
        return redirect(url_for('login'))

    # Fetch visit counts from the database
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT page, visit_count FROM visits")
        visit_data = cursor.fetchall()

    return render_template('visit_counts.html', visit_data=visit_data)

# Route for the homepage
@app.route('/homepage')
def homepage():
    recipes = get_recipes()  # Now this should work since get_recipes is defined above
    return render_template('homepage.html', recipes=recipes)

# Function to fetch recipes
def get_recipes():
    recipes = [
        {'title': 'Pancakes', 'description': 'Fluffy and delicious.'},
        {'title': 'Omelette', 'description': 'Eggs with vegetables.'}
    ]
    return recipes

@app.route('/mazaqat.html')
def mazaqat_page():
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE category_id = 5")  # Assuming 5 is the 'mazaqat' category ID
        recipes = cursor.fetchall()

    # Update visit count for this page
    update_visit_count('mazaqat')

    return render_template('mazaqat.html', recipes=recipes)

# Route for the services page
@app.route('/serv')
@app.route('/serv.html')
def serv_page():
    return render_template('serv.html')  # Ensure the 'serv.html' file is in the templates folder


if __name__ == '__main__':
    app.run(debug=True)

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to the database and check the credentials
        with sqlite3.connect('database/recipes.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]  # Assuming first column is user ID
            session['username'] = user[1]  # Assuming second column is username
            is_admin = user[3]  # Assuming the is_admin column is at index 3

            # Check if user is admin
            if is_admin == 1:
                session['admin'] = True  # Set admin session if the user is an admin
                return redirect(url_for('admin_home'))  # Redirect to admin page
            else:
                session['admin'] = False  # Ensure normal user session is set
                return redirect(url_for('homepage'))  # Redirect to homepage for normal users
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


import random

def get_random_recipe():
    with sqlite3.connect('database/recipes.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recipes")
        recipes = cursor.fetchall()
    
    # اختيار وصفة عشوائية
    random_recipe = random.choice(recipes) if recipes else None
    return random_recipe

from flask import jsonify

@app.route('/spin_the_wheel', methods=['GET'])
def spin_the_wheel():
    recipe = get_random_recipe()  # جلب وصفة عشوائية من قاعدة البيانات
    
    if recipe:
        recipe_data = {
            'name': recipe[1],  # Assuming name is at index 1
            'description': recipe[2],  # Assuming description is at index 2
            'ingredients': recipe[3],  # Assuming ingredients is at index 3
            'instructions': recipe[4],  # Assuming instructions is at index 4
        }
    else:
        recipe_data = None

    return jsonify(recipe_data)  # إرجاع البيانات بتنسيق JSON
