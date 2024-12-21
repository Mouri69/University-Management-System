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
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    # Check if the user exists in the students table
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        # Query to check if the user is a student
        cursor.execute("SELECT * FROM students WHERE email = ? AND password = ?", (email, password))
        student = cursor.fetchone()

        # Query to check if the user is an instructor
        cursor.execute("SELECT * FROM Instructors WHERE email = ? AND password = ?", (email, password))
        instructor = cursor.fetchone()

        conn.close()

        # Check if student data was found
        if student:
            return "Logged in as Student"
        # Check if instructor data was found
        elif instructor:
            # Fetch all students' data when logged in as instructor
            try:
                conn = pyodbc.connect(CONNECTION_STRING)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM students")  # Query to get all students' data
                students_data = cursor.fetchall()
                conn.close()

                # Pass the student data to the template and display it
                return render_template('instructor_dashboard.html', students=students_data)
            except Exception as e:
                return f"An error occurred while fetching student data: {e}"
        else:
            return "Invalid email or password"
    except Exception as e:
        return f"An error occurred: {e}"

# Route to handle displaying the sign-up choice page (GET method)
@app.route('/signup-choice', methods=['GET'])
def signup_choice():
    return render_template('signup.html')

# Route to handle form submission for role selection (POST method)
@app.route('/signup-choice', methods=['POST'])
def handle_signup_choice():
    role = request.form['role']
    if role == 'student':
        return redirect(url_for('signup_student'))
    elif role == 'instructor':
        return redirect(url_for('signup_instructor'))
    else:
        return "Invalid role selection", 400

# Route for Student Sign Up page
@app.route('/signup-student')
def signup_student():
    return render_template('signup-student.html')

# Route for Instructor Sign Up page
@app.route('/signup-instructor')
def signup_instructor():
    return render_template('signup-instructor.html')

# Route to handle Student Sign Up form submission
@app.route('/signup-student', methods=['POST'])
def submit_student():
    # Get form data for student
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    address = request.form['address']
    birthdate = request.form['birthdate']

    # Insert student data into the database
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        query = """
        INSERT INTO students (Fname, Lname, email, phone, password, address, birthdate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (fname, lname, email, phone, password, address, birthdate))
        conn.commit()
        conn.close()
        return "Student data inserted successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

# Route to handle Instructor Sign Up form submission
@app.route('/signup-instructor', methods=['POST'])
def submit_instructor():
    # Get form data for instructor
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    password = request.form['password']
    phone = request.form['phone']
    address = request.form['address']
    birthdate = request.form['birthdate']

    # Insert instructor data into the database
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        query = """
        INSERT INTO Instructors (Fname, Lname, email, password, phone, address, birthdate)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (fname, lname, email, password, phone, address, birthdate))
        conn.commit()
        conn.close()
        return "Instructor data inserted successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)
