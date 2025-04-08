from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for session management

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check credentials (you can store admin credentials in the database)
        if username == 'admin' and password == 'password123':  # Replace with your credentials
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

# Route for the admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('login'))

    # Connect to the database
    conn = sqlite3.connect('database/recipes.db')
    cursor = conn.cursor()

    # Fetch all recipes
    cursor.execute("SELECT * FROM recipes")
    recipes = cursor.fetchall()
    conn.close()

    return render_template('admin.html', recipes=recipes)

# Route to log out
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))
# route to delete a recipe

@app.route('/delete_recipe/<int:recipe_id>')
def delete_recipe(recipe_id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database/recipes.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))
# route to add a new recipe 

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if not session.get('admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        category_id = request.form['category_id']  # Assuming you have categories

        conn = sqlite3.connect('database/recipes.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recipes (name, description, ingredients, instructions, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, ingredients, instructions, category_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    return render_template('add_recipe.html')

# Route to edit a recipe
@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if not session.get('admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database/recipes.db')
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
        conn.close()
        return redirect(url_for('admin_dashboard'))

    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

if __name__ == '__main__':
    app.run(debug=True)