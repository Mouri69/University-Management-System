from flask import Flask, render_template, request
import pyodbc

app = Flask(__name__)

# SQL Server database configuration
SQL_SERVER = 'MOURI\\SQLEXPRESS'  # Use double backslashes for escaping
DATABASE = 'University'

# Connection string for SQL Server (Trusted Connection)
CONNECTION_STRING = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    # Get form data
    fname = request.form['fname']
    lname = request.form['lname']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    birthdate = request.form['birthdate']

    # Insert data into the database
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        query = """
        INSERT INTO students ( Fname, Lname, email, phone, address, birthdate)
        VALUES ( ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, ( fname, lname, email, phone, address, birthdate))
        conn.commit()
        conn.close()
        return "Data inserted successfully!"
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == '__main__':
    app.run(debug=True)
