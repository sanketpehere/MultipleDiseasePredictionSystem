from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# MySQL Configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Set MySQL password if any
app.config['MYSQL_DB'] = 'projectdb'
app.config['SECRET_KEY'] = '151220'  # Fixed secret key for session handling

mysql = MySQL(app)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')

# Login Route with POST handling for login functionality


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Create a cursor
        cur = mysql.connection.cursor()

        # Fetch user by email
        cur.execute("SELECT * FROM users WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()

        if user:
            if check_password_hash(user[4], password):
                session['logged_in'] = True
                session['user_id'] = user[0]
                session['user_name'] = user[1]

                flash('Login successful!', 'success')

                # Redirect to the disease prediction input page
                return redirect(url_for('predict'))
            else:
                flash('Incorrect password. Please try again.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('No account found with that email address.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

# Signup Route


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup'))

        # Hash the password
        hashed_password = generate_password_hash(
            password, method='pbkdf2:sha256')

        # Create a cursor
        cur = mysql.connection.cursor()

        try:
            # Insert user into the database
            cur.execute("INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                        (name, email, phone, hashed_password))
            mysql.connection.commit()  # Save changes to the database
            flash('Signup successful! You can now log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            mysql.connection.rollback()  # Rollback in case of error
            flash(f"Error: {str(e)}", 'danger')
            return redirect(url_for('signup'))
        finally:
            cur.close()  # Close the cursor

    return render_template('signup.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Handle prediction logic here (e.g., retrieve form data for disease prediction)

        pass  # Replace with your prediction logic

    return render_template('predict.html')


# Logout Route


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
