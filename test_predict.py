#student performance prediction and analysis
from flask import Flask, render_template, jsonify, request, redirect, session, flash, url_for
import mysql.connector
import hashlib
import datetime
import joblib
import numpy as np
import json  # Import json for proper handling of lists in URLs

app = Flask(__name__)
app.secret_key = "lbs2025"  # Secret key for session and flash messages

# Load ML Model and Thresholds
model = joblib.load('student_model.pkl')
thresholds = joblib.load('thresholds.pkl')

# Database Connection Function
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Athira2004@",  # Change this to your MySQL password
        database="student_performance_prediction_and_analysis"
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['loginUsername']
        password = hashlib.sha256(request.form['loginPassword'].encode()).hexdigest()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['username'] = username  # Store user session
            login_time = datetime.datetime.now()
            cursor.execute("INSERT INTO userlogin (username, login_time) VALUES (%s, %s)", (username, login_time))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))
        else:
            conn.close()
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['registerUsername']
    email = request.form['registerEmail']
    password = hashlib.sha256(request.form['registerPassword'].encode()).hexdigest()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        conn.commit()
        conn.close()
        flash("Registration Successful! You can now log in.", "success")
        return redirect(url_for('login'))
    except mysql.connector.IntegrityError:
        conn.close()
        flash("Username or Email already exists. Try a different one.", "error")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'GET':
        # Render the prediction form if accessed via GET
        return render_template('prediction.html')

    if 'username' not in session:
        flash("Please log in to make predictions.", "error")
        return redirect(url_for('login'))

    username = session['username']
    student_id = request.form.get('studentid')

    # Validate Student ID
    if not student_id:
        flash("Student ID is required.", "error")
        return redirect(url_for('home'))

    try:
        # Preprocess categorical values
        gender = 1 if request.form.get('gender', '').lower() == 'male' else 0
        age = int(request.form.get('age', 0))
        address = 1 if request.form.get('address', '').lower() == 'urban' else 0
        parent_education = int(request.form.get('parentEducation', 0))
        travel_time = int(request.form.get('travelTime', 0))
        study_time = int(request.form.get('studyTime', 0))
        failures = int(request.form.get('failures', 0))
        extra_classes = 1 if request.form.get('extraClasses', '').lower() == 'yes' else 0
        extra_curricular = 1 if request.form.get('extraCurricular', '').lower() == 'yes' else 0
        internet_access = 1 if request.form.get('internetAccess', '').lower() == 'yes' else 0
        health = int(request.form.get('health', 0))
        absences = int(request.form.get('absences', 0))
        sub1_mark = int(request.form.get('subject1Mark', 0))
        sub2_mark = int(request.form.get('subject2Mark', 0))
        sub3_mark = int(request.form.get('subject3Mark', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Store student data
        cursor.execute("""
            INSERT INTO student (student_id, username, gender, age, address, parent_education, travel_time, study_time,
                                 failures, extra_classes, extra_curricular, internet_access, health, absences, sub1_mark,
                                 sub2_mark, sub3_mark)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                gender = VALUES(gender), age = VALUES(age), address = VALUES(address),
                parent_education = VALUES(parent_education), travel_time = VALUES(travel_time),
                study_time = VALUES(study_time), failures = VALUES(failures),
                extra_classes = VALUES(extra_classes), extra_curricular = VALUES(extra_curricular),
                internet_access = VALUES(internet_access), health = VALUES(health),
                absences = VALUES(absences), sub1_mark = VALUES(sub1_mark),
                sub2_mark = VALUES(sub2_mark), sub3_mark = VALUES(sub3_mark)
        """, (student_id, username, gender, age, address, parent_education, travel_time, study_time, failures,
              extra_classes, extra_curricular, internet_access, health, absences, sub1_mark, sub2_mark, sub3_mark))
        conn.commit()

        # Fetch stored student data
        cursor.execute("""
            SELECT gender, age, address, parent_education, travel_time, study_time, failures, extra_classes, extra_curricular,
                   internet_access, health, absences, sub1_mark, sub2_mark, sub3_mark
            FROM student
            WHERE student_id = %s
        """, (student_id,))
        student_data = cursor.fetchone()

        if not student_data:
            conn.close()
            flash("Student data not found.", "error")
            return redirect(url_for('home'))

        student_data = np.array(student_data, dtype=np.float64).reshape(1, -1)

        # Predict marks
        predicted_marks = model.predict(student_data)[0]

        weak_subjects = []
        if predicted_marks[0] < thresholds['Sub1']:
            weak_subjects.append("Subject 1")
        if predicted_marks[1] < thresholds['Sub2']:
            weak_subjects.append("Subject 2")
        if predicted_marks[2] < thresholds['Sub3']:
            weak_subjects.append("Subject 3")

        weak_subjects_str = ", ".join(weak_subjects) if weak_subjects else "None"

        # Store prediction results in session for result page
        session['prediction_results'] = {
            'sub1': int(predicted_marks[0]),
            'sub2': int(predicted_marks[1]),
            'sub3': int(predicted_marks[2]),
            'weak_subjects': weak_subjects_str
        }

        # Store prediction results in database
        cursor.execute("""
            INSERT INTO prediction (username, studentid, predicted_sub1, predicted_sub2, predicted_sub3, weak_subject)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                predicted_sub1 = VALUES(predicted_sub1),
                predicted_sub2 = VALUES(predicted_sub2),
                predicted_sub3 = VALUES(predicted_sub3),
                weak_subject = VALUES(weak_subject)
        """, (username, student_id, int(predicted_marks[0]), int(predicted_marks[1]), int(predicted_marks[2]), weak_subjects_str))
        conn.commit()
        conn.close()

        # Return JSON response
        return jsonify({
            "success": True,
            "predicted_marks": {
                "sub1": int(predicted_marks[0]),
                "sub2": int(predicted_marks[1]),
                "sub3": int(predicted_marks[2])
            }
        })

    except mysql.connector.Error as db_err:
        flash("Database error occurred. Please try again.", "error")
    except Exception as e:
        flash("Unexpected error occurred. Please try again.", "error")

    return redirect(url_for('home'))

@app.route('/result')
def result():
    # Check if prediction results exist in session
    if 'prediction_results' not in session:
        flash("No prediction results available.", "error")
        return redirect(url_for('predict'))

    # Get prediction results from session
    prediction_results = session.pop('prediction_results', None)

    return render_template('result.html', results=prediction_results)

if __name__ == '__main__':
     app.run(debug=True)