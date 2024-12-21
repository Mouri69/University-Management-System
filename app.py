from flask import Flask, render_template, request, redirect, url_for
import pyodbc

app = Flask(__name__)

# SQL Server database configuration
SQL_SERVER = 'MOURI\\SQLEXPRESS'  # Use double backslashes for escaping
DATABASE = 'University'

# Connection string for SQL Server (Trusted Connection)
CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes'

@app.route('/')
def home():
    return render_template('signup.html')

@app.route('/signup-choice', methods=['POST'])
def signup_choice():
    role = request.form['role']
    if role == 'student':
        return redirect(url_for('signup_student'))
    elif role == 'instructor':
        return redirect(url_for('signup_instructor'))
    else:
        return "Invalid role selection"

@app.route('/signup-student')
def signup_student():
    return render_template('signup-student.html')

@app.route('/signup-instructor')
def signup_instructor():
    return render_template('signup-instructor.html')

@app.route('/signup-student', methods=['POST'])
def submit_student():
    # Get form data for student
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    birthdate = request.form['birthdate']

    # Insert student data into the database
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        query = """
        INSERT INTO students (Fname, Lname, email, phone, address, birthdate)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (fname, lname, email, phone, address, birthdate))
        conn.commit()
        conn.close()
        return "Student data inserted successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/submit-instructor', methods=['POST'])
def submit_instructor():
    # Get form data for instructor
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    birthdate = request.form['birthdate']

    # Insert instructor data into the database
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        query = """
        INSERT INTO instructors (Fname, Lname, email, phone, address ,birthdate)
        VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (fname, lname, email, phone, address ,birthdate))
        conn.commit()
        conn.close()
        return "Instructor data inserted successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)
