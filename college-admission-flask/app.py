from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import date

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_db_connection():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )

class User(UserMixin):
    def __init__(self, id, email, is_admin=False):
        self.id = id
        self.email = email
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        is_admin = user.get('user_type') == 'Admin'
        return User(user['user_id'], user['email'], is_admin)
    return None

# ====================== ADMISSION FORM ======================
@app.route('/admission_form', methods=['GET', 'POST'])
def admission_form():
    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Extract all form data
            last_name = request.form['last_name']
            first_name = request.form['first_name']
            middle_name = request.form['middle_name']
            name_suffix = request.form.get('name_suffix')
            birth_date = request.form['birth_date']
            sex_id = request.form['sex_id']
            civil_status_id = request.form['civil_status_id']
            citizenship = request.form.get('citizenship', 'Filipino')
            primary_contact_number = request.form['primary_contact_number']
            primary_contact_email = request.form['primary_contact_email']
            password = request.form['password']                    # ← This was missing
            track_strand = request.form['track_strand']
            course_first_choice = request.form['course_first_choice']
            course_second_choice = request.form.get('course_second_choice')

            house_number = request.form['house_number']
            street = request.form['street']
            subdivision = request.form.get('subdivision')
            town = request.form['town']
            city = request.form['city']
            province = request.form['province']
            postal_code = request.form['postal_code']

            # Check duplicate email
            cursor.execute("SELECT email FROM users WHERE email = %s", (primary_contact_email,))
            if cursor.fetchone():
                flash('This email is already registered. Please use a different email.', 'error')
                return redirect(url_for('admission_form'))

            # Insert Applicant
            cursor.execute("INSERT INTO applicants () VALUES ()")
            applicant_id = cursor.lastrowid

            # Personal Information
            cursor.execute("""
                INSERT INTO personal_information 
                (applicant_id, last_name, first_name, middle_name, name_suffix, birth_date, 
                 sex_id, civil_status_id, citizenship, primary_contact_number, 
                 primary_contact_email, track_strand, course_first_choice, course_second_choice, status_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (applicant_id, last_name, first_name, middle_name, name_suffix, birth_date,
                  sex_id, civil_status_id, citizenship, primary_contact_number,
                  primary_contact_email, track_strand, course_first_choice, course_second_choice))

            # Address
            cursor.execute("""
                INSERT INTO address 
                (applicant_id, house_number, street, subdivision, town, city, province, postal_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (applicant_id, house_number, street, subdivision, town, city, province, postal_code))

            # Educational Attainment
            education_list = [
                ("Elementary", "elem_school", "elem_address", "elem_type", "elem_from", "elem_to"),
                ("Junior High", "hs_school", "hs_address", "hs_type", "hs_from", "hs_to"),
                ("Senior High", "shs_school", "shs_address", "shs_type", "shs_from", "shs_to"),
                ("College", "college_school", "college_address", "college_type", "college_from", "college_to")
            ]

            for level_name, school_field, addr_field, type_field, from_field, to_field in education_list:
                school_name = request.form.get(school_field)
                if school_name and school_name.strip():
                    education_level_id = {"Elementary":1, "Junior High":2, "Senior High":3, "College":4}.get(level_name)
                    education_type_id = 1 if request.form.get(type_field) == "Public" else 2

                    cursor.execute("""
                        INSERT INTO educational_attainment 
                        (applicant_id, education_level_id, school_name, school_address, 
                         education_type_id, year_attended_from, year_attended_to)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (applicant_id, education_level_id, school_name,
                          request.form.get(addr_field), education_type_id,
                          request.form.get(from_field), request.form.get(to_field)))

            # User Account
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (applicant_id, email, password, user_type)
                VALUES (%s, %s, %s, 'User')
            """, (applicant_id, primary_contact_email, hashed_password))

            # Transferee (optional)
            if request.form.get('course'):
                cursor.execute("""
                    INSERT INTO college_transferees 
                    (applicant_id, course, reason_for_transfer, gwa, date_filed, lrn)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (applicant_id, request.form.get('course'), request.form.get('reason_for_transfer'),
                      request.form.get('gwa'), date.today(), request.form.get('lrn')))

            conn.commit()
            print("✅ Application submitted successfully!")
            conn.close()
            return redirect(url_for('admission_form', success=1, id=applicant_id))

        except Exception as e:
            print("❌ Error submitting application:", str(e))
            flash('Error submitting application. Please check all fields.', 'error')
            return redirect(url_for('admission_form'))

    return render_template('admission-form.html')
    

# ====================== EDIT APPLICATION ======================
@app.route('/edit_application', methods=['GET', 'POST'])
@login_required
def edit_application():
    if current_user.is_admin:
        flash('Admins cannot edit this way.', 'error')
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.*, a.* 
        FROM personal_information p
        LEFT JOIN address a ON p.applicant_id = a.applicant_id
        WHERE p.primary_contact_email = %s
    """, (current_user.email,))
    application = cursor.fetchone()

    if not application:
        flash('No application found.', 'error')
        conn.close()
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        try:
            print("Form Data:", dict(request.form))

            cursor.execute("""
                UPDATE personal_information 
                SET last_name = %s, first_name = %s, middle_name = %s, name_suffix = %s,
                    birth_date = %s, sex_id = %s, civil_status_id = %s, citizenship = %s,
                    primary_contact_number = %s
                WHERE applicant_id = %s
            """, (
                request.form.get('last_name'), request.form.get('first_name'),
                request.form.get('middle_name'), request.form.get('name_suffix'),
                request.form.get('birth_date'), request.form.get('sex_id'),
                request.form.get('civil_status_id'), request.form.get('citizenship'),
                request.form.get('primary_contact_number'), application['applicant_id']
            ))

            cursor.execute("""
                UPDATE address 
                SET house_number = %s, street = %s, subdivision = %s,
                    town = %s, city = %s, province = %s, postal_code = %s
                WHERE applicant_id = %s
            """, (
                request.form.get('house_number'), request.form.get('street'),
                request.form.get('subdivision'), request.form.get('town'),
                request.form.get('city'), request.form.get('province'),
                request.form.get('postal_code'), application['applicant_id']
            ))

            conn.commit()
            print("✅ UPDATE SUCCESSFUL!")
            flash('✅ Application updated successfully!', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception as e:
            conn.rollback()
            print("❌ ERROR:", str(e))
            flash('❌ Failed to update application.', 'error')

    conn.close()
    return render_template('edit_application.html', application=application)

# ====================== LOGIN ======================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            is_admin = user.get('user_type') == 'Admin'
            login_user(User(user['user_id'], user['email'], is_admin))
            
            if is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('index.html')

# ====================== DASHBOARDS ======================
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, s.status, a.*
        FROM personal_information p 
        JOIN applicant_status s ON p.status_id = s.status_id 
        LEFT JOIN address a ON p.applicant_id = a.applicant_id
        WHERE p.primary_contact_email = %s
    """, (current_user.email,))
    application = cursor.fetchone()
    conn.close()
    return render_template('user_dashboard.html', application=application)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('user_dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Statistics
        cursor.execute("SELECT COUNT(*) as total FROM applicants")
        total = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as pending FROM personal_information WHERE status_id = 1")
        pending = cursor.fetchone()['pending']

        cursor.execute("SELECT COUNT(*) as approved FROM personal_information WHERE status_id = 2")
        approved = cursor.fetchone()['approved']

        # Personal Information
        cursor.execute("""
            SELECT p.*, s.status 
            FROM personal_information p 
            JOIN applicant_status s ON p.status_id = s.status_id 
            ORDER BY p.applicant_id DESC
        """)
        personal_info = cursor.fetchall()

        # Address
        cursor.execute("SELECT * FROM address ORDER BY applicant_id DESC")
        addresses = cursor.fetchall()

        # Educational Attainment (This was missing!)
        cursor.execute("""
            SELECT * FROM educational_attainment 
            ORDER BY applicant_id DESC
        """)
        education = cursor.fetchall()

        # College Transferees
        cursor.execute("SELECT * FROM college_transferees ORDER BY applicant_id DESC")
        transferees = cursor.fetchall()

    except Exception as e:
        print("Database Error in Admin Dashboard:", e)
        personal_info = addresses = education = transferees = []
        total = pending = approved = 0

    finally:
        conn.close()

    return render_template('admin_dashboard.html', 
                         total=total, 
                         pending=pending, 
                         approved=approved,
                         personal_info=personal_info, 
                         addresses=addresses,
                         education=education,           # ← Added this
                         transferees=transferees)

@app.route('/admin/update_status', methods=['POST'])
@login_required
def update_status():
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('admin_dashboard'))

    applicant_id = request.form.get('applicant_id')
    status_id = request.form.get('status_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal_information SET status_id = %s WHERE applicant_id = %s", 
                   (status_id, applicant_id))
    conn.commit()
    conn.close()

    flash('Status updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)