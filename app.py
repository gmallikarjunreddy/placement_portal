from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_key_for_development')

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Add template context processor for current year
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'placement_portal')
}

# Database connection function
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Function to initialize database
def init_db():
    try:
        # First try to connect to MySQL server without specifying a database
        db_config_no_db = db_config.copy()
        db_config_no_db.pop('database')
        conn = mysql.connector.connect(**db_config_no_db)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.execute(f"USE {db_config['database']}")
        
        # Create tables
        create_tables_sql = [
            """
            CREATE TABLE IF NOT EXISTS Department (
                department_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                hod VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Student (
                student_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                department_id INT,
                cgpa DECIMAL(3,2),
                graduation_year INT,
                contact_number VARCHAR(15),
                resume_path VARCHAR(255),
                FOREIGN KEY (department_id) REFERENCES Department(department_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Company (
                company_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                description TEXT,
                industry VARCHAR(100),
                website VARCHAR(255),
                contact_email VARCHAR(100),
                contact_number VARCHAR(15)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Skills (
                skill_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(100)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Student_Skills (
                student_id INT,
                skill_id INT,
                proficiency_level VARCHAR(50),
                PRIMARY KEY (student_id, skill_id),
                FOREIGN KEY (student_id) REFERENCES Student(student_id),
                FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Opportunity (
                opportunity_id INT PRIMARY KEY AUTO_INCREMENT,
                company_id INT,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                type ENUM('internship', 'job') NOT NULL,
                posted_date DATE,
                deadline DATE,
                salary DECIMAL(10,2),
                location VARCHAR(100),
                requirements TEXT,
                FOREIGN KEY (company_id) REFERENCES Company(company_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Opportunity_Skills (
                opportunity_id INT,
                skill_id INT,
                is_required BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (opportunity_id, skill_id),
                FOREIGN KEY (opportunity_id) REFERENCES Opportunity(opportunity_id),
                FOREIGN KEY (skill_id) REFERENCES Skills(skill_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Application (
                application_id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT,
                opportunity_id INT,
                application_date DATE,
                status ENUM('applied', 'shortlisted', 'rejected', 'hired') DEFAULT 'applied',
                remarks TEXT,
                FOREIGN KEY (student_id) REFERENCES Student(student_id),
                FOREIGN KEY (opportunity_id) REFERENCES Opportunity(opportunity_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Interview (
                interview_id INT PRIMARY KEY AUTO_INCREMENT,
                application_id INT,
                schedule_date DATETIME,
                venue VARCHAR(255),
                interviewer VARCHAR(100),
                feedback TEXT,
                result ENUM('pending', 'selected', 'rejected') DEFAULT 'pending',
                FOREIGN KEY (application_id) REFERENCES Application(application_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Admin (
                admin_id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Settings (
                id INT PRIMARY KEY,
                site_name VARCHAR(100),
                admin_email VARCHAR(100),
                max_file_size INT,
                min_cgpa DECIMAL(3,2),
                max_applications INT,
                application_deadline_days INT,
                smtp_server VARCHAR(100),
                smtp_port INT,
                smtp_username VARCHAR(100),
                smtp_password VARCHAR(255),
                session_timeout INT,
                max_login_attempts INT,
                enable_2fa BOOLEAN
            )
            """
        ]
        
        for sql in create_tables_sql:
            cursor.execute(sql)
        
        # Check if Department table is empty
        cursor.execute("SELECT COUNT(*) FROM Department")
        count = cursor.fetchone()[0]
        
        # Insert sample data if empty
        if count == 0:
            # Insert sample departments
            departments = [
                ('Computer Science', 'Dr. Smith'),
                ('Electrical Engineering', 'Dr. Johnson'),
                ('Mechanical Engineering', 'Dr. Williams'),
                ('Civil Engineering', 'Dr. Brown'),
                ('Information Technology', 'Dr. Davis')
            ]
            cursor.executemany("INSERT INTO Department (name, hod) VALUES (%s, %s)", departments)
            
            # Insert sample skills
            skills = [
                ('Python', 'Programming'),
                ('Java', 'Programming'),
                ('C++', 'Programming'),
                ('JavaScript', 'Web Development'),
                ('React', 'Web Development')
            ]
            cursor.executemany("INSERT INTO Skills (name, category) VALUES (%s, %s)", skills)
            
            # Insert a sample company
            sample_password = generate_password_hash('password')
            cursor.execute("""
                INSERT INTO Company (name, email, password, description, industry, website, contact_email, contact_number)
                VALUES ('TechCorp', 'hr@techcorp.com', %s, 'Leading technology solutions provider', 'Information Technology', 
                        'www.techcorp.com', 'hr@techcorp.com', '1234567890')
            """, (sample_password,))
            
            conn.commit()
            print("Database initialized with sample data")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"Database initialization error: {err}")

# Initialize the database
init_db()

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Student registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        department_id = request.form['department_id']
        cgpa = request.form['cgpa']
        graduation_year = request.form['graduation_year']
        contact_number = request.form['contact_number']
        
        # Handle resume upload (optional during registration)
        resume_path = None
        if 'resume' in request.files and request.files['resume'].filename != '':
            resume = request.files['resume']
            filename = secure_filename(resume.filename)
            # Ensure uploads directory exists
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            resume_path = os.path.join(UPLOAD_FOLDER, filename)
            resume.save(resume_path)
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO Student (name, email, password, department_id, cgpa, 
                                    graduation_year, contact_number, resume_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, email, hashed_password, department_id, 
                                   cgpa, graduation_year, contact_number, resume_path))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    # Get departments for the registration form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Department")
    departments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('register.html', departments=departments)

# Company registration
@app.route('/company/register', methods=['GET', 'POST'])
def company_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        industry = request.form['industry']
        website = request.form['website']
        contact_email = request.form['contact_email']
        contact_number = request.form['contact_number']
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO Company (name, email, password, industry, website, contact_email, contact_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, email, hashed_password, industry, website, contact_email, contact_number))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('company_login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('company/register.html')

# Company login
@app.route('/company/login', methods=['GET', 'POST'])
def company_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM Company WHERE email = %s", (email,))
        company = cursor.fetchone()
        
        if company and check_password_hash(company['password'], password):
            session['user_id'] = company['company_id']
            session['user_type'] = 'company'
            session['name'] = company['name']
            flash('Login successful!', 'success')
            return redirect(url_for('company_dashboard'))
        
        flash('Invalid email or password', 'danger')
        cursor.close()
        conn.close()
        
    return render_template('company/login.html')

# Company dashboard
@app.route('/company/dashboard')
def company_dashboard():
    if 'user_id' not in session or session['user_type'] != 'company':
        flash('Please login first', 'warning')
        return redirect(url_for('company_login'))
    
    company_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get company details
    cursor.execute("SELECT * FROM Company WHERE company_id = %s", (company_id,))
    company = cursor.fetchone()
    
    # Get company's opportunities
    cursor.execute("""
        SELECT o.*, COUNT(a.application_id) as application_count
        FROM Opportunity o
        LEFT JOIN Application a ON o.opportunity_id = a.opportunity_id
        WHERE o.company_id = %s
        GROUP BY o.opportunity_id
        ORDER BY o.posted_date DESC
    """, (company_id,))
    opportunities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('company/dashboard.html', 
                          company=company, 
                          opportunities=opportunities)

# Add new opportunity
@app.route('/company/opportunity/add', methods=['GET', 'POST'])
def add_opportunity():
    if 'user_id' not in session or session['user_type'] != 'company':
        flash('Please login first', 'warning')
        return redirect(url_for('company_login'))
    
    if request.method == 'POST':
        company_id = session['user_id']
        title = request.form['title']
        description = request.form['description']
        type = request.form['type']
        deadline = request.form['deadline']
        salary = request.form['salary']
        location = request.form['location']
        requirements = request.form['requirements']
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO Opportunity (company_id, title, description, type, posted_date, deadline, 
                                      salary, location, requirements)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (company_id, title, description, type, datetime.date.today(), 
                                 deadline, salary, location, requirements))
            conn.commit()
            flash('Opportunity posted successfully!', 'success')
            return redirect(url_for('company_dashboard'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('company/add_opportunity.html')

# View applications for an opportunity
@app.route('/company/opportunity/<int:opportunity_id>/applications')
def view_applications(opportunity_id):
    if 'user_id' not in session or session['user_type'] != 'company':
        flash('Please login first', 'warning')
        return redirect(url_for('company_login'))
    
    company_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verify the opportunity belongs to the company
    cursor.execute("""
        SELECT * FROM Opportunity 
        WHERE opportunity_id = %s AND company_id = %s
    """, (opportunity_id, company_id))
    opportunity = cursor.fetchone()
    
    if not opportunity:
        flash('Opportunity not found', 'danger')
        return redirect(url_for('company_dashboard'))
    
    # Get applications for this opportunity
    cursor.execute("""
        SELECT a.*, s.student_id, s.name as student_name, s.email as student_email, 
               s.cgpa, s.graduation_year, d.name as department_name
        FROM Application a
        JOIN Student s ON a.student_id = s.student_id
        JOIN Department d ON s.department_id = d.department_id
        WHERE a.opportunity_id = %s
        ORDER BY a.application_date DESC
    """, (opportunity_id,))
    applications = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('company/applications.html', 
                          opportunity=opportunity,
                          applications=applications)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if it's a student login
        cursor.execute("SELECT * FROM Student WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['student_id']
            session['user_type'] = 'student'
            session['name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        
        flash('Invalid email or password', 'danger')
        cursor.close()
        conn.close()
        
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# Student dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get student details with department name
    cursor.execute("""
        SELECT s.*, d.name as department_name
        FROM Student s
        JOIN Department d ON s.department_id = d.department_id
        WHERE s.student_id = %s
    """, (student_id,))
    student = cursor.fetchone()
    
    # Get student's skills
    cursor.execute("""
        SELECT s.*, ss.proficiency_level 
        FROM Skills s
        LEFT JOIN Student_Skills ss ON s.skill_id = ss.skill_id AND ss.student_id = %s
        ORDER BY s.category, s.name
    """, (student_id,))
    student_skills = cursor.fetchall()
    
    # Get student applications
    cursor.execute("""
        SELECT a.*, o.title, c.name as company_name 
        FROM Application a
        JOIN Opportunity o ON a.opportunity_id = o.opportunity_id
        JOIN Company c ON o.company_id = c.company_id
        WHERE a.student_id = %s
        ORDER BY a.application_date DESC
    """, (student_id,))
    applications = cursor.fetchall()
    
    # Get available opportunities
    cursor.execute("""
        SELECT o.*, c.name as company_name
        FROM Opportunity o
        JOIN Company c ON o.company_id = c.company_id
        WHERE o.deadline >= CURDATE()
        ORDER BY o.posted_date DESC
    """)
    opportunities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('student/dashboard.html', 
                          student=student, 
                          student_skills=student_skills,
                          applications=applications,
                          opportunities=opportunities)

# View opportunity details
@app.route('/opportunity/<int:opportunity_id>')
def view_opportunity(opportunity_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get opportunity details
    cursor.execute("""
        SELECT o.*, c.name as company_name, c.description as company_description
        FROM Opportunity o
        JOIN Company c ON o.company_id = c.company_id
        WHERE o.opportunity_id = %s
    """, (opportunity_id,))
    opportunity = cursor.fetchone()
    
    # Get required skills
    cursor.execute("""
        SELECT s.name, os.is_required
        FROM Opportunity_Skills os
        JOIN Skills s ON os.skill_id = s.skill_id
        WHERE os.opportunity_id = %s
    """, (opportunity_id,))
    skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('opportunity_details.html', 
                          opportunity=opportunity, 
                          skills=skills)

# Apply for opportunity
@app.route('/apply/<int:opportunity_id>', methods=['GET', 'POST'])
def apply_for_opportunity(opportunity_id):
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    
    if request.method == 'POST':
        # Check if resume is uploaded
        if 'resume' not in request.files or request.files['resume'].filename == '':
            flash('Resume is required for application', 'danger')
            return redirect(url_for('apply_for_opportunity', opportunity_id=opportunity_id))
        
        resume = request.files['resume']
        filename = secure_filename(resume.filename)
        
        # Ensure uploads directory exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        resume_path = os.path.join(UPLOAD_FOLDER, filename)
        resume.save(resume_path)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if already applied
            cursor.execute("""
                SELECT * FROM Application 
                WHERE student_id = %s AND opportunity_id = %s
            """, (student_id, opportunity_id))
            
            if cursor.fetchone():
                flash('You have already applied for this opportunity', 'warning')
            else:
                # Update student's resume path
                cursor.execute("""
                    UPDATE Student 
                    SET resume_path = %s 
                    WHERE student_id = %s
                """, (resume_path, student_id))
                
                # Insert application
                cursor.execute("""
                    INSERT INTO Application (student_id, opportunity_id, application_date)
                    VALUES (%s, %s, %s)
                """, (student_id, opportunity_id, datetime.date.today()))
                
                conn.commit()
                flash('Application submitted successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
        
        return redirect(url_for('student_dashboard'))
    
    # Get opportunity details for confirmation
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.*, c.name as company_name
        FROM Opportunity o
        JOIN Company c ON o.company_id = c.company_id
        WHERE o.opportunity_id = %s
    """, (opportunity_id,))
    opportunity = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('apply.html', opportunity=opportunity)

# Add new department
@app.route('/add_department', methods=['POST'])
def add_department():
    try:
        # Get department details from JSON payload
        data = request.get_json()
        department_name = data.get('department_name')
        hod_name = data.get('hod_name', '')
        
        if not department_name:
            return jsonify({'success': False, 'message': 'Department name is required'})
        
        # Insert new department
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "INSERT INTO Department (name, hod) VALUES (%s, %s)"
        cursor.execute(query, (department_name, hod_name))
        conn.commit()
        
        # Get the ID of the newly created department
        department_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'department_id': department_id,
            'message': 'Department added successfully'
        })
    
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': str(err)})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# View student resume
@app.route('/student/<int:student_id>/resume')
def view_student_resume(student_id):
    if 'user_id' not in session:
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get student details and resume path
    cursor.execute("""
        SELECT s.*, d.name as department_name
        FROM Student s
        JOIN Department d ON s.department_id = d.department_id
        WHERE s.student_id = %s
    """, (student_id,))
    student = cursor.fetchone()
    
    if not student:
        flash('Student not found', 'danger')
        if session['user_type'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('company_dashboard'))
    
    if not student['resume_path'] or not os.path.exists(student['resume_path']):
        flash('Resume not available', 'warning')
        if session['user_type'] == 'student':
            return redirect(url_for('student_dashboard'))
        else:
            return redirect(url_for('company_dashboard'))
    
    # Check if the user has permission to view this resume
    if session['user_type'] == 'student' and session['user_id'] != student_id:
        flash('You do not have permission to view this resume', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Return the resume file for preview
    return send_file(student['resume_path'], mimetype='application/pdf', as_attachment=False)

# Edit student profile
@app.route('/student/profile/edit', methods=['GET', 'POST'])
def edit_student_profile():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get student details
    cursor.execute("""
        SELECT s.*, d.name as department_name
        FROM Student s
        JOIN Department d ON s.department_id = d.department_id
        WHERE s.student_id = %s
    """, (student_id,))
    student = cursor.fetchone()
    
    # Get all departments for the dropdown
    cursor.execute("SELECT * FROM Department")
    departments = cursor.fetchall()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        department_id = request.form['department_id']
        cgpa = request.form['cgpa']
        graduation_year = request.form['graduation_year']
        contact_number = request.form['contact_number']
        
        # Handle resume upload
        resume_path = student['resume_path']  # Keep existing resume path by default
        if 'resume' in request.files and request.files['resume'].filename != '':
            resume = request.files['resume']
            filename = secure_filename(resume.filename)
            # Ensure uploads directory exists
            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            resume_path = os.path.join(UPLOAD_FOLDER, filename)
            resume.save(resume_path)
        
        # Update password if provided
        password_update = ""
        params = [name, email, department_id, cgpa, graduation_year, contact_number, resume_path, student_id]
        
        if request.form['password']:
            hashed_password = generate_password_hash(request.form['password'])
            password_update = ", password = %s"
            params.insert(-1, hashed_password)  # Insert before student_id
        
        try:
            query = f"""
                UPDATE Student 
                SET name = %s, email = %s, department_id = %s, cgpa = %s, 
                    graduation_year = %s, contact_number = %s, resume_path = %s{password_update}
                WHERE student_id = %s
            """
            cursor.execute(query, params)
            conn.commit()
            
            # Update session name
            session['name'] = name
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_dashboard'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
    
    cursor.close()
    conn.close()
    
    return render_template('student/edit_profile.html', student=student, departments=departments)

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM Admin WHERE email = %s", (email,))
        admin = cursor.fetchone()
        
        if admin and check_password_hash(admin['password'], password):
            session['user_id'] = admin['admin_id']
            session['user_type'] = 'admin'
            session['name'] = admin['name']
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        
        flash('Invalid email or password', 'danger')
        cursor.close()
        conn.close()
        
    return render_template('admin/login.html')

# Admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) as total_students FROM Student")
    total_students = cursor.fetchone()['total_students']
    
    cursor.execute("SELECT COUNT(*) as total_companies FROM Company")
    total_companies = cursor.fetchone()['total_companies']
    
    cursor.execute("SELECT COUNT(*) as total_opportunities FROM Opportunity")
    total_opportunities = cursor.fetchone()['total_opportunities']
    
    cursor.execute("SELECT COUNT(*) as total_applications FROM Application")
    total_applications = cursor.fetchone()['total_applications']
    
    # Get department statistics
    cursor.execute("""
        SELECT d.name, COUNT(a.application_id) as application_count
        FROM Department d
        LEFT JOIN Student s ON d.department_id = s.department_id
        LEFT JOIN Application a ON s.student_id = a.student_id
        GROUP BY d.department_id, d.name
    """)
    department_stats = cursor.fetchall()
    
    # Get placement status statistics
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM Application
        GROUP BY status
    """)
    placement_stats = cursor.fetchall()
    
    # Get recent activities
    cursor.execute("""
        SELECT 
            a.application_date as date,
            'Application' as activity_type,
            s.name as user_name,
            CONCAT('Applied for ', o.title) as details
        FROM Application a
        JOIN Student s ON a.student_id = s.student_id
        JOIN Opportunity o ON a.opportunity_id = o.opportunity_id
        ORDER BY a.application_date DESC
        LIMIT 10
    """)
    recent_activities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    stats = {
        'total_students': total_students,
        'total_companies': total_companies,
        'total_opportunities': total_opportunities,
        'total_applications': total_applications
    }
    
    return render_template('admin/dashboard.html',
                          stats=stats,
                          department_stats=department_stats,
                          placement_stats=placement_stats,
                          recent_activities=recent_activities)

# Admin manage departments
@app.route('/admin/departments')
def admin_manage_departments():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Department")
    departments = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/departments.html', departments=departments)

# Admin manage users
@app.route('/admin/users')
def admin_manage_users():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get students
    cursor.execute("""
        SELECT s.*, d.name as department_name
        FROM Student s
        JOIN Department d ON s.department_id = d.department_id
    """)
    students = cursor.fetchall()
    
    # Get companies
    cursor.execute("SELECT * FROM Company")
    companies = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/users.html', students=students, companies=companies)

# Admin delete user
@app.route('/admin/delete_user/<string:user_type>/<int:user_id>', methods=['POST'])
def admin_delete_user(user_type, user_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if user_type == 'student':
            cursor.execute("DELETE FROM Student WHERE student_id = %s", (user_id,))
        elif user_type == 'company':
            cursor.execute("DELETE FROM Company WHERE company_id = %s", (user_id,))
        
        conn.commit()
        flash('User deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_manage_users'))

# Admin add department
@app.route('/admin/add_department', methods=['POST'])
def admin_add_department():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    name = request.form['name']
    hod = request.form['hod']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Department (name, hod) VALUES (%s, %s)", (name, hod))
        conn.commit()
        flash('Department added successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_manage_departments'))

# Admin delete department
@app.route('/admin/delete_department/<int:department_id>', methods=['POST'])
def admin_delete_department(department_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM Department WHERE department_id = %s", (department_id,))
        conn.commit()
        flash('Department deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_manage_departments'))

# Create admin user
@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO Admin (name, email, password) VALUES (%s, %s, %s)", 
                         (name, email, hashed_password))
            conn.commit()
            flash('Admin user created successfully!', 'success')
            return redirect(url_for('admin_login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin/create_admin.html')

# Admin manage opportunities
@app.route('/admin/opportunities')
def admin_manage_opportunities():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT o.*, c.name as company_name
        FROM Opportunity o
        JOIN Company c ON o.company_id = c.company_id
        ORDER BY o.posted_date DESC
    """)
    opportunities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/opportunities.html', opportunities=opportunities)

# Admin manage skills
@app.route('/admin/skills')
def admin_manage_skills():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM Skills ORDER BY category, name")
    skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/skills.html', skills=skills)

# Admin add skill
@app.route('/admin/add_skill', methods=['POST'])
def admin_add_skill():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    name = request.form['name']
    category = request.form['category']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO Skills (name, category) VALUES (%s, %s)", (name, category))
        conn.commit()
        flash('Skill added successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_manage_skills'))

# Admin delete skill
@app.route('/admin/delete_skill/<int:skill_id>', methods=['POST'])
def admin_delete_skill(skill_id):
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM Skills WHERE skill_id = %s", (skill_id,))
        conn.commit()
        flash('Skill deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_manage_skills'))

# Admin reports
@app.route('/admin/reports')
def admin_reports():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get placement statistics by department
    cursor.execute("""
        SELECT 
            d.name as department_name,
            COUNT(DISTINCT s.student_id) as total_students,
            COUNT(DISTINCT a.application_id) as total_applications,
            COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.application_id END) as placed_students
        FROM Department d
        LEFT JOIN Student s ON d.department_id = s.department_id
        LEFT JOIN Application a ON s.student_id = a.student_id
        GROUP BY d.department_id, d.name
    """)
    department_stats = cursor.fetchall()
    
    # Get company-wise placement statistics
    cursor.execute("""
        SELECT 
            c.name as company_name,
            COUNT(DISTINCT o.opportunity_id) as total_opportunities,
            COUNT(DISTINCT a.application_id) as total_applications,
            COUNT(DISTINCT CASE WHEN a.status = 'hired' THEN a.application_id END) as total_hires
        FROM Company c
        LEFT JOIN Opportunity o ON c.company_id = o.company_id
        LEFT JOIN Application a ON o.opportunity_id = a.opportunity_id
        GROUP BY c.company_id, c.name
    """)
    company_stats = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/reports.html', 
                          department_stats=department_stats,
                          company_stats=company_stats)

# Admin settings
@app.route('/admin/settings', methods=['GET'])
def admin_settings():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT * FROM Settings WHERE id = 1')
    settings = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('admin/settings.html', settings=settings)

# Admin update settings
@app.route('/admin/settings/update', methods=['POST'])
def admin_update_settings():
    if 'user_id' not in session or session['user_type'] != 'admin':
        flash('Please login first', 'warning')
        return redirect(url_for('admin_login'))
    
    try:
        # Get form data
        site_name = request.form.get('site_name')
        admin_email = request.form.get('admin_email')
        max_file_size = request.form.get('max_file_size')
        min_cgpa = request.form.get('min_cgpa')
        max_applications = request.form.get('max_applications')
        application_deadline_days = request.form.get('application_deadline_days')
        smtp_server = request.form.get('smtp_server')
        smtp_port = request.form.get('smtp_port')
        smtp_username = request.form.get('smtp_username')
        smtp_password = request.form.get('smtp_password')
        session_timeout = request.form.get('session_timeout')
        max_login_attempts = request.form.get('max_login_attempts')
        enable_2fa = 'enable_2fa' in request.form

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if settings exist
        cursor.execute('SELECT id FROM Settings WHERE id = 1')
        settings_exist = cursor.fetchone()
        
        if settings_exist:
            # Update existing settings
            cursor.execute('''
                UPDATE Settings SET 
                site_name = %s, admin_email = %s, max_file_size = %s,
                min_cgpa = %s, max_applications = %s, application_deadline_days = %s,
                smtp_server = %s, smtp_port = %s, smtp_username = %s,
                smtp_password = %s, session_timeout = %s, max_login_attempts = %s,
                enable_2fa = %s
                WHERE id = 1
            ''', (site_name, admin_email, max_file_size, min_cgpa, max_applications,
                 application_deadline_days, smtp_server, smtp_port, smtp_username,
                 smtp_password, session_timeout, max_login_attempts, enable_2fa))
        else:
            # Insert new settings
            cursor.execute('''
                INSERT INTO Settings (
                    id, site_name, admin_email, max_file_size, min_cgpa,
                    max_applications, application_deadline_days, smtp_server,
                    smtp_port, smtp_username, smtp_password, session_timeout,
                    max_login_attempts, enable_2fa
                ) VALUES (
                    1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            ''', (site_name, admin_email, max_file_size, min_cgpa, max_applications,
                 application_deadline_days, smtp_server, smtp_port, smtp_username,
                 smtp_password, session_timeout, max_login_attempts, enable_2fa))
        
        conn.commit()
        flash('Settings updated successfully', 'success')
        
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_settings'))

# Student manage skills
@app.route('/student/skills', methods=['GET', 'POST'])
def student_manage_skills():
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        skill_id = request.form.get('skill_id')
        proficiency_level = request.form.get('proficiency_level')
        
        try:
            # Check if this is a new skill
            if skill_id == 'new':
                new_skill_name = request.form.get('new_skill_name')
                new_skill_category = request.form.get('new_skill_category')
                
                if not new_skill_name or not new_skill_category:
                    flash('Please provide both skill name and category', 'danger')
                    return redirect(url_for('student_manage_skills'))
                
                # Insert the new skill
                cursor.execute("""
                    INSERT INTO Skills (name, category) 
                    VALUES (%s, %s)
                """, (new_skill_name, new_skill_category))
                
                # Get the ID of the newly created skill
                skill_id = cursor.lastrowid
                
                # Add the skill to the student
                cursor.execute("""
                    INSERT INTO Student_Skills (student_id, skill_id, proficiency_level)
                    VALUES (%s, %s, %s)
                """, (student_id, skill_id, proficiency_level))
                
                conn.commit()
                flash('New skill added successfully!', 'success')
                return redirect(url_for('student_manage_skills'))
            
            # For existing skills
            cursor.execute("""
                SELECT * FROM Student_Skills 
                WHERE student_id = %s AND skill_id = %s
            """, (student_id, skill_id))
            
            if cursor.fetchone():
                # Update existing skill
                cursor.execute("""
                    UPDATE Student_Skills 
                    SET proficiency_level = %s 
                    WHERE student_id = %s AND skill_id = %s
                """, (proficiency_level, student_id, skill_id))
            else:
                # Add new skill
                cursor.execute("""
                    INSERT INTO Student_Skills (student_id, skill_id, proficiency_level)
                    VALUES (%s, %s, %s)
                """, (student_id, skill_id, proficiency_level))
            
            conn.commit()
            flash('Skill updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
    
    # Get all available skills
    cursor.execute("SELECT * FROM Skills ORDER BY category, name")
    all_skills = cursor.fetchall()
    
    # Get student's current skills
    cursor.execute("""
        SELECT s.*, ss.proficiency_level 
        FROM Skills s
        LEFT JOIN Student_Skills ss ON s.skill_id = ss.skill_id AND ss.student_id = %s
        ORDER BY s.category, s.name
    """, (student_id,))
    student_skills = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('student/skills.html', 
                          all_skills=all_skills,
                          student_skills=student_skills)

# Student delete skill
@app.route('/student/delete_skill/<int:skill_id>', methods=['POST'])
def student_delete_skill(skill_id):
    if 'user_id' not in session or session['user_type'] != 'student':
        flash('Please login first', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM Student_Skills 
            WHERE student_id = %s AND skill_id = %s
        """, (student_id, skill_id))
        conn.commit()
        flash('Skill removed successfully', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('student_manage_skills'))

if __name__ == '__main__':
    app.run(debug=True) 