from flask import Flask, render_template, request, redirect, url_for
import pyodbc
from datetime import date

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

    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        # Query to check if the user is a student
        cursor.execute("SELECT * FROM students WHERE email = ? AND password = ?", (email, password))
        student = cursor.fetchone()

        # Query to check if the user is an instructor
        cursor.execute("SELECT * FROM Instructors WHERE email = ? AND password = ?", (email, password))
        instructor = cursor.fetchone()

        # Check if student data was found
        if student:
            # Convert the pyodbc.Row object to a dictionary
            student_dict = {
                'student_id': student.student_id,
                'fname': student.fname,
                'lname': student.lname,
                'email': student.email,
                'phone': student.phone,
                'address': student.address,
                'birthdate': student.birthdate,
                'total_absence': student.total_absence
            }

            # Fetch courses for the student
            cursor.execute("""
                SELECT c.course_id, c.course_name, c.course_code
                FROM Courses c
                JOIN StudentCourses sc ON c.course_id = sc.course_id
                WHERE sc.student_id = ?
            """, student.student_id)
            
            courses = [{"id": row.course_id, "name": row.course_name, "code": row.course_code} for row in cursor.fetchall()]

            conn.close()
            return render_template('student_dashboard.html', student=student_dict, courses=courses)
        
        # Check if instructor data was found
        elif instructor:
            # Fetch all students' data when logged in as instructor
            cursor.execute("SELECT * FROM students")  # Query to get all students' data
            students_data = cursor.fetchall()
            conn.close()

            # Pass the student data to the template and display it
            return render_template('instructor_dashboard.html', students=students_data)
        else:
            conn.close()
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

@app.route('/instructor-dashboard')
def instructor_dashboard():
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Explicitly specify columns and their order
        query = """
        SELECT 
        s.student_id,
        s.fname,
        s.lname,
        s.email,
        COALESCE(CAST((SELECT COUNT(*) 
                        FROM attendance a 
                        WHERE a.student_id = s.student_id 
                        AND a.status = 1) AS INT), 0) as total_absences,
        COALESCE((SELECT TOP 1 status
                FROM attendance 
                WHERE student_id = s.student_id 
                AND CONVERT(DATE, date) = CONVERT(DATE, GETDATE())
                ), 0) as today_status
    FROM students s
    ORDER BY s.student_id
        """
        
        cursor.execute(query)
        students = cursor.fetchall()
        conn.close()

        return render_template('instructor_dashboard.html', students=students)
    
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/update-attendance', methods=['POST'])
def update_attendance():
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        form_data = request.form
        for key in form_data:
            if key.startswith('status_'):
                student_id = key.split('_')[1]
                is_absent = 1 if form_data[key] == 'on' else 0  # Check if the checkbox was checked

                # Check if there's already an attendance record for today
                check_query = """
                SELECT attendance_id 
                FROM attendance 
                WHERE student_id = ? 
                AND CONVERT(DATE, date) = CONVERT(DATE, GETDATE())
                """
                cursor.execute(check_query, student_id)
                existing_record = cursor.fetchone()

                if existing_record:  # If attendance exists, update status
                    update_query = """
                    UPDATE attendance
                    SET status = ?
                    WHERE attendance_id = ?
                    """
                    cursor.execute(update_query, (is_absent, existing_record[0]))

                else:  # If no attendance exists, insert a new record
                    insert_query = """
                    INSERT INTO attendance (student_id, status, date)
                    VALUES (?, ?, GETDATE())
                    """
                    cursor.execute(insert_query, (student_id, is_absent))

                # Increment total_absence in students table if marked absent
                if is_absent == 1:
                    print(f"Incrementing total_absence for student_id: {student_id}")
                    increment_absence_query = """
                    UPDATE students
                    SET total_absence = total_absence + 1
                    WHERE student_id = ?
                    """
                    cursor.execute(increment_absence_query, student_id)

        # Commit changes to the database
        conn.commit()

        # Re-fetch student data to display updated absences
        fetch_students_query = """
        SELECT 
            s.student_id,
            s.fname,
            s.lname,
            s.email,
            COALESCE((SELECT COUNT(*) 
                      FROM attendance a 
                      WHERE a.student_id = s.student_id 
                      AND a.status = 1), 0) as total_absences,
            COALESCE((SELECT TOP 1 status
                      FROM attendance 
                      WHERE student_id = s.student_id 
                      AND CONVERT(DATE, date) = CONVERT(DATE, GETDATE())
                    ), 0) as today_status
        FROM students s
        ORDER BY s.student_id
        """
        cursor.execute(fetch_students_query)
        students = cursor.fetchall()

        conn.close()

        # Redirect to dashboard with updated data
        return render_template('login.html', students=students)

    except Exception as e:
        return f"An error occurred: {e}"



@app.route('/save-attendance', methods=['POST'])
def save_attendance():
    try:
        # Get a list of student IDs and their status from the form
        students_data = request.form.getlist('student_data')  # Assuming 'student_data' is a list of student info
        
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        for student_data in students_data:
            student_id = student_data['student_id']
            status = student_data['status']
            
            # Query to check if there's already an attendance record for the current date
            query = """
            SELECT attendance_id FROM attendance
            WHERE student_id = ? AND CONVERT(DATE, date) = CONVERT(DATE, GETDATE());
            """
            
            cursor.execute(query, (student_id,))
            result = cursor.fetchone()

            if result:
                # If attendance record exists, update the status
                update_query = """
                UPDATE attendance
                SET status = ?
                WHERE attendance_id = ?;
                """
                cursor.execute(update_query, (status, result.attendance_id))
            else:
                # If no attendance record exists for this student, insert a new record
                insert_query = """
                INSERT INTO attendance (student_id, status, date)
                VALUES (?, ?, CONVERT(DATE, GETDATE()));
                """
                cursor.execute(insert_query, (student_id, status))

        conn.commit()
        conn.close()
        print("hello")
        return redirect(url_for('instructor_dashboard'))
    
    except Exception as e:
        return f"An error occurred: {e}"



if __name__ == '__main__':
    app.run(debug=True)
