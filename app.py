from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import joblib

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
                session['user_email'] = user[2]
                session['user_phone'] = user[3]
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


@app.route('/predict/heart', methods=['POST'])
def predict_heart():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        # Retrieve form data
        user_details = {
            "age": int(request.form['age']),
            "gender": "Male" if int(request.form['gender']) == 1 else "Female",
            "height": int(request.form['height']),
            "weight": int(request.form['weight']),
            "systolic_bp": int(request.form['systolic_bp']),
            "diastolic_bp": int(request.form['diastolic_bp']),
            "cholesterol": {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal"
            }[int(request.form['cholesterol'])],
            "glucose": {
                1: "Normal",
                2: "Above Normal",
                3: "Well Above Normal"
            }[int(request.form['glucose'])],
            "smoking": "Yes" if int(request.form['smoking']) == 1 else "No",
            "alcohol": "Yes" if int(request.form['alcohol']) == 1 else "No",
            "physical_activity": "Yes" if int(request.form['physical_activity']) == 1 else "No"
        }

        # Get selected algorithms
        selected_algorithms = request.form.getlist('algorithms')
        if not selected_algorithms:
            flash('Please select at least one algorithm.', 'warning')
            return redirect(url_for('predict'))

        # Prepare input for prediction
        features = [[
            user_details["age"],
            1 if user_details["gender"] == "Male" else 2,
            user_details["height"],
            user_details["weight"],
            user_details["systolic_bp"],
            user_details["diastolic_bp"],
            1 if user_details["cholesterol"] == "Normal" else 2 if user_details["cholesterol"] == "Above Normal" else 3,
            1 if user_details["glucose"] == "Normal" else 2 if user_details["glucose"] == "Above Normal" else 3,
            1 if user_details["smoking"] == "Yes" else 0,
            1 if user_details["alcohol"] == "Yes" else 0,
            1 if user_details["physical_activity"] == "Yes" else 0
        ]]

        # List to store results
        results = []

        # Evaluate selected models
        for idx, algorithm in enumerate(selected_algorithms, start=1):
            model_path = f'models/heart/{algorithm}_heart_model.pkl'
            try:
                # Load the model
                model = joblib.load(model_path)

                # Make prediction
                prediction = model.predict(features)[0]
                # Assuming predict_proba is implemented
                probability = model.predict_proba(features)[0][1] * 100

                # Map prediction to result
                final_result = "Positive" if prediction == 1 else "Negative"

                # Append to results
                results.append({
                    "sr_no": idx,
                    "disease": "Heart Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": f"{probability:.2f}%",
                    "result": final_result
                })
            except Exception as e:
                results.append({
                    "sr_no": idx,
                    "disease": "Heart Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": "N/A",
                    "result": f"Error: {str(e)}"
                })
        # Pass user details and results to a new template
        return render_template('results.html', user_details=user_details, results=results,  user_name=session.get('user_name'),
                               user_email=session.get('user_email'),
                               user_phone=session.get('user_phone'))

    except Exception as e:
        flash(f"Error during prediction: {e}", 'danger')
        return redirect(url_for('predict'))


# Handling diabetes form details
@app.route('/predict/diabetes', methods=['POST'])
def predict_diabetes():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        # Retrieve form data
        user_details = {
            "age": int(request.form['age']),
            "gender": request.form['gender'],
            "hypertension": "Yes" if int(request.form['hypertension']) == 1 else "No",
            "heart_disease": "Yes" if int(request.form['heart_disease']) == 1 else "No",
            "smoking_history": request.form['smoking_history'],
            "bmi": float(request.form['bmi']),
            "hemoglobin_a1c": float(request.form['hemoglobin_a1c']),
            "blood_glucose": int(request.form['blood_glucose']),
        }

        # Get selected algorithms
        selected_algorithms = request.form.getlist('algorithms')
        if not selected_algorithms:
            flash('Please select at least one algorithm.', 'warning')
            return redirect(url_for('predict'))

        # Prepare input for prediction
        features = [[
            user_details["age"],
            1 if user_details["gender"] == "Male" else 0,
            1 if user_details["hypertension"] == "Yes" else 0,
            1 if user_details["heart_disease"] == "Yes" else 0,
            0 if user_details["smoking_history"] == "No Info" else
            (1 if user_details["smoking_history"] == "never" else
             2 if user_details["smoking_history"] == "former" else
             3 if user_details["smoking_history"] == "current" else 4),
            user_details["bmi"],
            user_details["hemoglobin_a1c"],
            user_details["blood_glucose"]
        ]]

        # List to store results
        results = []

        # Evaluate selected models
        for idx, algorithm in enumerate(selected_algorithms, start=1):
            model_path = f'models/diabetes/{algorithm}_model.pkl'
            try:
                # Load the model
                model = joblib.load(model_path)

                # Make prediction
                prediction = model.predict(features)[0]
                # Assuming predict_proba is implemented
                probability = model.predict_proba(features)[0][1] * 100

                # Map prediction to result
                final_result = "Positive" if prediction == 1 else "Negative"

                # Append to results
                results.append({
                    "sr_no": idx,
                    "disease": "Diabetes",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": f"{probability:.2f}%",
                    "result": final_result
                })
            except Exception as e:
                results.append({
                    "sr_no": idx,
                    "disease": "Diabetes",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": "N/A",
                    "result": f"Error: {str(e)}"
                })

        # Pass user details and results to a new template
        return render_template('results_diabetes.html', user_details=user_details, results=results, user_name=session.get('user_name'),
                               user_email=session.get('user_email'),
                               user_phone=session.get('user_phone'))

    except Exception as e:
        flash(f"Error during prediction: {e}", 'danger')
        return redirect(url_for('predict'))


@app.route('/predict/liver', methods=['POST'])
def predict_liver():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        # Retrieve form data
        user_details = {
            "age": int(request.form['age']),
            "gender": request.form['gender'],
            "total_bilirubin": float(request.form['total_bilirubin']),
            "direct_bilirubin": float(request.form['direct_bilirubin']),
            "alkaline_phosphotase": int(request.form['alkaline_phosphotase']),
            "alamine_aminotransferase": int(request.form['alamine_aminotransferase']),
            "aspartate_aminotransferase": int(request.form['aspartate_aminotransferase']),
            "total_proteins": float(request.form['total_proteins']),
            "albumin": float(request.form['albumin']),
            "albumin_globulin_ratio": float(request.form['albumin_globulin_ratio']),
        }

        # Get selected algorithms
        selected_algorithms = request.form.getlist('algorithms')
        if not selected_algorithms:
            flash('Please select at least one algorithm.', 'warning')
            return redirect(url_for('predict'))

        # Prepare input for prediction
        features = [[
            user_details["age"],
            1 if user_details["gender"] == "Male" else 0,
            user_details["total_bilirubin"],
            user_details["direct_bilirubin"],
            user_details["alkaline_phosphotase"],
            user_details["alamine_aminotransferase"],
            user_details["aspartate_aminotransferase"],
            user_details["total_proteins"],
            user_details["albumin"],
            user_details["albumin_globulin_ratio"],
        ]]

        # List to store results
        results = []

        # Evaluate selected models
        for idx, algorithm in enumerate(selected_algorithms, start=1):
            model_path = f'models/liver/{algorithm}_model.pkl'
            try:
                # Load the model
                model = joblib.load(model_path)

                # Make prediction
                prediction = model.predict(features)[0]
                print(prediction)
                # Assuming predict_proba is implemented
                probability = model.predict_proba(features)[0][1] * 100

                # Map prediction to result
                final_result = "Positive" if prediction == 1 else "Negative"

                # Append to results
                results.append({
                    "sr_no": idx,
                    "disease": "Liver Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": f"{probability:.2f}%",
                    "result": final_result
                })
            except Exception as e:
                results.append({
                    "sr_no": idx,
                    "disease": "Liver Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": "N/A",
                    "result": f"Error: {str(e)}"
                })

        # Pass user details and results to a new template
        return render_template('results_liver.html', user_details=user_details, results=results, user_name=session.get('user_name'),
                               user_email=session.get('user_email'),
                               user_phone=session.get('user_phone'))

    except Exception as e:
        flash(f"Error during prediction: {e}", 'danger')
        return redirect(url_for('predict'))


@app.route('/predict/kidney', methods=['POST'])
def predict_kidney():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'danger')
        return redirect(url_for('login'))

    try:
        # Retrieve form data
        user_details = {
            "age": float(request.form['age']),
            "blood_pressure": float(request.form['blood_pressure']),
            "specific_gravity": float(request.form['specific_gravity']),
            "albumin": float(request.form['albumin']),
            "sugar": float(request.form['sugar']),
            "red_blood_cells": request.form['red_blood_cells'],
            "pus_cells": request.form['pus_cells'],
            "pus_cell_clumps": request.form['pus_cell_clumps'],
            "bacteria": request.form['bacteria'],
            "blood_glucose_random": float(request.form['blood_glucose_random']),
            "blood_urea": float(request.form['blood_urea']),
            "serum_creatinine": float(request.form['serum_creatinine']),
            "sodium": float(request.form['sodium']),
            "potassium": float(request.form['potassium']),
            "hemoglobin": float(request.form['hemoglobin']),
            "pcv": float(request.form['pcv']),
            "white_blood_cells": float(request.form['white_blood_cells']),
            "red_blood_cells_count": float(request.form['red_blood_cells_count']),
            "hypertension": request.form['hypertension'],
            "diabetes_mellitus": request.form['diabetes_mellitus'],
            "cad": request.form['cad'],
            "appetite": request.form['appetite'],
            "pedal_edema": request.form['pedal_edema'],
            "anemia": request.form['anemia']
        }

        # Get selected algorithms
        selected_algorithms = request.form.getlist('algorithms')
        if not selected_algorithms:
            flash('Please select at least one algorithm.', 'warning')
            return redirect(url_for('predict'))

        # Prepare input for prediction
        features = [[
            user_details["age"],
            user_details["blood_pressure"],
            user_details["specific_gravity"],
            user_details["albumin"],
            user_details["sugar"],
            1 if user_details["red_blood_cells"] == "normal" else 0,
            1 if user_details["pus_cells"] == "normal" else 0,
            1 if user_details["pus_cell_clumps"] == "present" else 0,
            1 if user_details["bacteria"] == "present" else 0,
            user_details["blood_glucose_random"],
            user_details["blood_urea"],
            user_details["serum_creatinine"],
            user_details["sodium"],
            user_details["potassium"],
            user_details["hemoglobin"],
            user_details["pcv"],
            user_details["white_blood_cells"],
            user_details["red_blood_cells_count"],
            1 if user_details["hypertension"] == "yes" else 0,
            1 if user_details["diabetes_mellitus"] == "yes" else 0,
            1 if user_details["cad"] == "yes" else 0,
            1 if user_details["appetite"] == "good" else 0,
            1 if user_details["pedal_edema"] == "yes" else 0,
            1 if user_details["anemia"] == "yes" else 0
        ]]

        # List to store results
        results = []

        # Evaluate selected models
        for idx, algorithm in enumerate(selected_algorithms, start=1):
            model_path = f'models/kidney/{algorithm}_kidney_model.pkl'
            try:
                # Load the model
                model = joblib.load(model_path)

                # Make prediction
                prediction = model.predict(features)[0]
                # Assuming predict_proba is implemented
                probability = model.predict_proba(features)[0][1] * 100

                # Map prediction to result
                final_result = "Positive" if prediction == 1 else "Negative"

                # Append to results
                results.append({
                    "sr_no": idx,
                    "disease": "Kidney Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": f"{probability:.2f}%",
                    "result": final_result
                })
            except Exception as e:
                results.append({
                    "sr_no": idx,
                    "disease": "Kidney Disease",
                    "model": algorithm.replace('_', ' ').title(),
                    "probability": "N/A",
                    "result": f"Error: {str(e)}"
                })

        # Pass user details and results to a new template
        return render_template('results_kidney.html', user_details=user_details, results=results, user_name=session.get('user_name'),
                               user_email=session.get('user_email'),
                               user_phone=session.get('user_phone'))

    except Exception as e:
        flash(f"Error during prediction: {e}", 'danger')
        return redirect(url_for('predict'))

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
