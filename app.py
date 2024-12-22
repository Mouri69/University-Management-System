from flask import Flask, render_template, request, redirect, url_for, flash, session
import pyodbc
from datetime import datetime

app = Flask(__name__)
app.secret_key= '1234567891234567'

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

        if student:
            # Store student ID in session
            session['student_id'] = student.student_id
            session['user_type'] = 'student'

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

            # Fetch enrolled courses for the student
            cursor.execute("""
                SELECT c.course_id, c.course_name, c.course_code
                FROM Courses c
                JOIN StudentCourses sc ON c.course_id = sc.course_id
                WHERE sc.student_id = ?
            """, student.student_id)
            
            enrolled_courses = [{"id": row.course_id, "name": row.course_name, "code": row.course_code} 
                              for row in cursor.fetchall()]

            conn.close()
            return render_template('student_dashboard.html', student=student_dict, enrolled_courses=enrolled_courses)
        
        elif instructor:
            session['student_id'] = instructor.student_id
            session['user_type'] = 'instructor'
            
            # Fetch all students' data
            cursor.execute("SELECT * FROM students")
            students_data = cursor.fetchall()
            conn.close()
            
            return render_template('instructor_dashboard.html', students=students_data)
        else:
            conn.close()
            flash('Invalid email or password')
            return redirect(url_for('home'))
            
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/student-dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Fetch student information
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (session['student_id'],))
        student = cursor.fetchone()
        
        # Convert to dictionary
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
        
        # Fetch enrolled courses
        cursor.execute("""
            SELECT c.course_id, c.course_name, c.course_code
            FROM Courses c
            JOIN StudentCourses sc ON c.course_id = sc.course_id
            WHERE sc.student_id = ?
        """, session['student_id'])
        
        enrolled_courses = [{"id": row.course_id, "name": row.course_name, "code": row.course_code} 
                          for row in cursor.fetchall()]
        
        conn.close()
        return render_template('student_dashboard.html', student=student_dict, enrolled_courses=enrolled_courses)
        
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/enrolled-courses')
def enrolled_courses():
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Fetch student information
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (session['student_id'],))
        student = cursor.fetchone()
        
        # Convert to dictionary
        student_dict = {
            'student_id': student.student_id,
            'fname': student.fname,
            'lname': student.lname
        }
        
        # Fetch enrolled courses
        cursor.execute("""
            SELECT c.course_id, c.course_name, c.course_code
            FROM Courses c
            JOIN StudentCourses sc ON c.course_id = sc.course_id
            WHERE sc.student_id = ?
        """, session['student_id'])
        
        enrolled_courses = [{"course_id": row.course_id, "course_name": row.course_name, "course_code": row.course_code} 
                          for row in cursor.fetchall()]
        
        # Fetch available courses (not enrolled)
        cursor.execute("""
            SELECT c.course_id, c.course_name, c.course_code
            FROM Courses c
            WHERE c.course_id NOT IN (
                SELECT course_id FROM StudentCourses WHERE student_id = ?
            )
        """, session['student_id'])
        
        available_courses = [{"course_id": row.course_id, "course_name": row.course_name, "course_code": row.course_code} 
                           for row in cursor.fetchall()]
        
        conn.close()
        return render_template('rolled-courses.html', 
                             student=student_dict,
                             enrolled_courses=enrolled_courses,
                             available_courses=available_courses)
                             
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/enroll-course/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Check if already enrolled
        cursor.execute("""
            SELECT * FROM StudentCourses 
            WHERE student_id = ? AND course_id = ?
        """, (session['student_id'], course_id))
        
        if cursor.fetchone():
            flash('You are already enrolled in this course')
        else:
            # Enroll the student
            cursor.execute("""
                INSERT INTO StudentCourses (student_id, course_id)
                VALUES (?, ?)
            """, (session['student_id'], course_id))
            conn.commit()
            flash('Successfully enrolled in the course')
        
        conn.close()
        return redirect(url_for('enrolled_courses'))
        
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/unenroll-course/<int:course_id>', methods=['POST'])
def unenroll_course(course_id):
    if 'student_id' not in session:
        return redirect(url_for('home'))
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        
        # Remove the enrollment
        cursor.execute("""
            DELETE FROM StudentCourses 
            WHERE student_id = ? AND course_id = ?
        """, (session['student_id'], course_id))
        
        conn.commit()
        conn.close()
        
        flash('Successfully unenrolled from the course')
        return redirect(url_for('enrolled_courses'))
        
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

@app.route('/remove_student/<int:student_id>', methods=['POST'])
def remove_student(student_id):
    print("Starting removal process for student_id:", student_id)

    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()

        # Check if the student exists
        cursor.execute("SELECT student_id FROM students WHERE student_id = ?", (student_id,))
        student = cursor.fetchone()
        if not student:
            print(f"No student found with ID: {student_id}")
            return "No student found with this ID", 400

        # Begin deletion process
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM StudentCourses WHERE student_id = ?", (student_id,))
        cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))

        # Commit changes
        conn.commit()

        return "Student removed successfully", 200  # Return success message for AJAX
        
    except Exception as e:
        conn.rollback()
        print(f"Error during removal: {e}")
        return "Error occurred during removal", 500
        
    finally:
        cursor.close()
        conn.close()


    
if __name__ == '__main__':
    app.run(debug=True)
