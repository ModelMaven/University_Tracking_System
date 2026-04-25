from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash, Response, send_file
import csv
import io
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import uuid
import random
from datetime import datetime, timedelta
import db
from geo import calculate_distance

app = Flask(__name__)
app.secret_key = 'super_secret_attendance_key_for_mvp' # Required for sessions

# Initialize DB on startup
with app.app_context():
    db.init_db()

# --- AUTH DECORATORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                return "Unauthorized access. Role required: " + role, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'ADMIN': return redirect(url_for('admin_dashboard'))
        if role == 'PROFESSOR': return redirect(url_for('prof_dashboard'))
        if role == 'STUDENT': return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user:
            if not user['password_hash']:
                flash('Your account has been created but you have not set a password. Please check your email for the setup link, or contact an admin.', 'error')
            elif check_password_hash(user['password_hash'], password):
                roles = [r.strip() for r in user['role'].split(',')]
                session['user_id'] = user['id']
                session['name'] = f"{user['first_name']} {user['last_name']}"
                session['available_roles'] = roles
                
                if len(roles) > 1:
                    return redirect(url_for('select_role'))
                else:
                    session['role'] = roles[0]
                    return redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'error')
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            token = str(uuid.uuid4())
            expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
            cursor.execute("INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user['id'], expires_at))
            conn.commit()
            
            # MOCK EMAIL
            reset_url = url_for('reset_password', token=token, _external=True)
            print(f"\n{'='*50}\n[MOCK EMAIL SENT TO {email}]\nSubject: Reset Your Password\nLink: {reset_url}\n{'='*50}\n")
            
            flash('If that email exists in our system, a password reset link has been sent.', 'success')
        else:
            flash('If that email exists in our system, a password reset link has been sent.', 'success')
            
        conn.close()
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token = ?", (token,))
    token_data = cursor.fetchone()
    
    if not token_data or datetime.datetime.strptime(token_data['expires_at'].split('.')[0], '%Y-%m-%d %H:%M:%S') < datetime.datetime.now():
        conn.close()
        flash('Invalid or expired password reset link.', 'error')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        new_password = request.form.get('password')
        hashed_pw = generate_password_hash(new_password)
        
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_pw, token_data['user_id']))
        cursor.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        
        flash('Your password has been successfully set! You can now log in.', 'success')
        return redirect(url_for('login'))
        
    conn.close()
    return render_template('reset_password.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/select_role')
def select_role():
    if 'user_id' not in session or 'available_roles' not in session:
        return redirect(url_for('login'))
    if len(session['available_roles']) == 1:
        session['role'] = session['available_roles'][0]
        return redirect(url_for('index'))
    return render_template('select_role.html', roles=session['available_roles'])

@app.route('/set_role', methods=['POST'])
def set_role():
    if 'user_id' not in session or 'available_roles' not in session:
        return redirect(url_for('login'))
    
    selected_role = request.form.get('role')
    if selected_role in session['available_roles']:
        session['role'] = selected_role
        return redirect(url_for('index'))
    return redirect(url_for('select_role'))

# --- ADMIN VIEWS ---
@app.route('/admin')
@login_required
@role_required('ADMIN')
def admin_dashboard():
    return render_template('admin_hub.html')

@app.route('/admin/students')
@login_required
@role_required('ADMIN')
def admin_students():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, email, role, assigned_admin_id FROM users")
    users = cursor.fetchall()
    
    # Also get all admins to populate the dropdown
    admins = [u for u in users if 'ADMIN' in u['role']]
    conn.close()
    return render_template('admin_students.html', users=users, admins=admins)

@app.route('/admin/professors')
@login_required
@role_required('ADMIN')
def admin_professors():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, email, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_professors.html', users=users)

@app.route('/admin/admins')
@login_required
@role_required('ADMIN')
def admin_admins():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, first_name, last_name, email, role FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_admins.html', users=users)

@app.route('/admin/courses')
@login_required
@role_required('ADMIN')
def admin_courses():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    
    cursor.execute("SELECT c.id, c.name, u.name as prof_name FROM courses c LEFT JOIN users u ON c.professor_id = u.id")
    courses = cursor.fetchall()
    conn.close()
    return render_template('admin_courses.html', users=users, courses=courses)

@app.route('/admin/reports')
@login_required
@role_required('ADMIN')
def admin_reports():
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.id, u.name as student_name, c.name as course_name, a.created_at, a.status 
        FROM attendance_records a
        JOIN users u ON a.student_id = u.id
        JOIN attendance_sessions s ON a.session_id = s.id
        JOIN courses c ON s.course_id = c.id
        ORDER BY a.created_at DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    
    formatted_records = []
    for r in records:
        formatted_records.append({
            'student_name': r['student_name'],
            'course_name': r['course_name'],
            'timestamp': r['created_at'],
            'status': r['status']
        })
        
    return render_template('admin_reports.html', records=formatted_records)

@app.route('/admin/create_user', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_create_user():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    role = request.form.get('role')
    
    conn = db.get_db()
    cursor = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO users (id, first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, first_name, last_name, email, None, role))
        
        token = str(uuid.uuid4())
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
        cursor.execute("INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_at))
        conn.commit()
        
        # MOCK EMAIL
        reset_url = url_for('reset_password', token=token, _external=True)
        print(f"\n{'='*50}\n[MOCK EMAIL SENT TO {email}]\nSubject: You've been invited! Set your password\nLink: {reset_url}\n{'='*50}\n")
        
        flash('User invited successfully! A password setup link has been sent to their email.', 'success')
    except Exception as e:
        flash('Error creating user: Email might exist.', 'error')
    finally:
        conn.close()
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/manual_reset', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_manual_reset():
    target_user_id = request.form.get('user_id')
    new_password = request.form.get('new_password')
    
    if target_user_id and new_password:
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_password), target_user_id))
        
        # Clear any pending tokens since admin set it
        cursor.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        flash('Password manually set successfully.', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/assign_admin', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_assign_admin():
    student_id = request.form.get('student_id')
    admin_id = request.form.get('admin_id')
    
    if student_id and admin_id:
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET assigned_admin_id = ? WHERE id = ?", (admin_id, student_id))
        conn.commit()
        conn.close()
        flash('Emergency admin assigned successfully.', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/update_roles', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_update_roles():
    target_user_id = request.form.get('user_id')
    roles = request.form.getlist('roles') # Checkboxes will send a list: ['ADMIN', 'PROFESSOR']
    
    if target_user_id and roles:
        roles_str = ','.join(roles)
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (roles_str, target_user_id))
        conn.commit()
        conn.close()
        flash('Roles updated successfully!', 'success')
    else:
        flash('Failed to update roles: Must select at least one role.', 'error')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/create_course', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_create_course():
    name = request.form.get('name')
    prof_id = request.form.get('professor_id')
    
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (id, name, professor_id) VALUES (?, ?, ?)",
        (str(uuid.uuid4()), name, prof_id))
    conn.commit()
    conn.close()
    flash('Course created successfully!', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/enroll', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_enroll():
    student_ids = request.form.getlist('student_ids')
    course_id = request.form.get('course_id')
    
    if not student_ids or not course_id:
        flash('Please select at least one student and a course.', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))

    conn = db.get_db()
    cursor = conn.cursor()
    success_count = 0
    error_count = 0

    for student_id in student_ids:
        try:
            cursor.execute("INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))
            success_count += 1
        except Exception:
            error_count += 1
            
    conn.commit()
    conn.close()
    
    flash(f'Enrolled {success_count} students successfully. {error_count} already enrolled.', 'success')
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/download_template')
@login_required
@role_required('ADMIN')
def download_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['First Name', 'Last Name', 'Email'])
    writer.writerow(['John', 'Doe', 'john@example.com'])
    writer.writerow(['Jane', 'Smith', 'jane@example.com'])
    
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='users_template.csv'
    )

@app.route('/admin/bulk_upload', methods=['POST'])
@login_required
@role_required('ADMIN')
def admin_bulk_upload():
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.referrer or url_for('admin_dashboard'))

    role = request.form.get('role', 'STUDENT').upper()

    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        
        headers = next(csv_input, None) # skip header
        conn = db.get_db()
        cursor = conn.cursor()
        success_count = 0
        error_count = 0
        
        for row in csv_input:
            if len(row) >= 3:
                first_name, last_name, email = row[0], row[1], row[2]
                
                try:
                    user_id = str(uuid.uuid4())
                    cursor.execute("INSERT INTO users (id, first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?, ?)",
                        (user_id, first_name, last_name, email, None, role))
                    
                    token = str(uuid.uuid4())
                    expires_at = datetime.datetime.now() + datetime.timedelta(hours=24)
                    cursor.execute("INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, expires_at))
                    
                    # MOCK EMAIL
                    reset_url = url_for('reset_password', token=token, _external=True)
                    print(f"\n{'='*50}\n[MOCK EMAIL SENT TO {email}]\nSubject: You've been invited! Set your password\nLink: {reset_url}\n{'='*50}\n")
                    
                    success_count += 1
                except Exception:
                    error_count += 1 # Likely duplicate email

        conn.commit()
        conn.close()
        
        flash(f'Bulk upload complete: {success_count} added and invited, {error_count} skipped/failed.', 'success')
    else:
        flash('Invalid file format. Please upload a CSV.', 'error')
        
    return redirect(request.referrer or url_for('admin_dashboard'))

# --- PROFESSOR VIEWS ---
@app.route('/professor')
@login_required
@role_required('PROFESSOR')
def prof_dashboard():
    conn = db.get_db()
    cursor = conn.cursor()
    
    # Get assigned courses
    cursor.execute("SELECT id, name FROM courses WHERE professor_id = ?", (session['user_id'],))
    courses = cursor.fetchall()
    
    return render_template('professor.html', courses=courses, name=session['name'])

@app.route('/api/assignments', methods=['POST'])
@login_required
@role_required('PROFESSOR')
def create_assignment():
    data = request.json
    course_id = data.get('course_id')
    title = data.get('title')
    desc = data.get('description')
    
    if not course_id or not title:
        return jsonify({"success": False, "message": "Missing fields"}), 400

    assignment_id = str(uuid.uuid4())
    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assignments (id, course_id, title, description) VALUES (?, ?, ?, ?)",
        (assignment_id, course_id, title, desc)
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Assignment created"})

# --- STUDENT VIEWS ---
@app.route('/student')
@login_required
@role_required('STUDENT')
def student_dashboard():
    conn = db.get_db()
    cursor = conn.cursor()
    
    # Get enrolled courses
    cursor.execute('''
        SELECT c.id, c.name, u.first_name || ' ' || u.last_name as prof_name 
        FROM courses c 
        JOIN enrollments e ON c.id = e.course_id 
        JOIN users u ON c.professor_id = u.id
        WHERE e.student_id = ?
    ''', (session['user_id'],))
    courses = cursor.fetchall()
    
    # Get assignments for enrolled courses
    cursor.execute('''
        SELECT a.title, a.description, c.name as course_name 
        FROM assignments a
        JOIN enrollments e ON a.course_id = e.course_id
        JOIN courses c ON a.course_id = c.id
        WHERE e.student_id = ?
        ORDER BY a.created_at DESC
    ''', (session['user_id'],))
    assignments = cursor.fetchall()
    
    # Get assigned admin contact
    cursor.execute('''
        SELECT a.first_name, a.last_name, a.email
        FROM users s
        LEFT JOIN users a ON s.assigned_admin_id = a.id
        WHERE s.id = ?
    ''', (session['user_id'],))
    admin_contact = cursor.fetchone()
    
    conn.close()
    return render_template('student.html', courses=courses, assignments=assignments, name=session['name'], admin_contact=admin_contact)

# --- ATTENDANCE API ---

def generate_otp():
    return str(random.randint(100000, 999999))

@app.route('/api/attendance/start', methods=['POST'])
@login_required
@role_required('PROFESSOR')
def start_attendance():
    data = request.json
    lat = data.get('latitude')
    lon = data.get('longitude')
    course_id = data.get('course_id')
    
    if lat is None or lon is None or not course_id:
        return jsonify({"success": False, "message": "Latitude, Longitude and Course ID required"}), 400

    otp = generate_otp()
    session_id = str(uuid.uuid4())
    prof_id = session['user_id']
    
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    conn = db.get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance_sessions (id, course_id, professor_id, otp, anchor_latitude, anchor_longitude, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, course_id, prof_id, otp, lat, lon, expires_at)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "data": {
            "otp": otp,
            "expires_at": expires_at.isoformat() + "Z"
        },
        "message": "Attendance session started successfully"
    }), 201

@app.route('/api/attendance/verify', methods=['POST'])
@login_required
@role_required('STUDENT')
def verify_attendance():
    data = request.json
    otp = data.get('otp')
    lat = data.get('latitude')
    lon = data.get('longitude')
    
    if not otp or lat is None or lon is None:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    conn = db.get_db()
    cursor = conn.cursor()
    
    # Validate OTP
    cursor.execute(
        "SELECT id, anchor_latitude, anchor_longitude, expires_at FROM attendance_sessions WHERE otp = ? ORDER BY created_at DESC LIMIT 1",
        (otp,)
    )
    att_session = cursor.fetchone()
    
    if not att_session:
        conn.close()
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

    expires_at = datetime.fromisoformat(att_session['expires_at'].split('.')[0])
    
    if datetime.utcnow() > expires_at:
        conn.close()
        return jsonify({"success": False, "message": "OTP has expired"}), 400

    # Distance check
    cursor.execute("SELECT value FROM settings WHERE key = 'attendance_radius_meters'")
    radius_row = cursor.fetchone()
    max_radius = float(radius_row['value']) if radius_row else 20.0

    distance = calculate_distance(
        float(lat), float(lon), 
        float(att_session['anchor_latitude']), float(att_session['anchor_longitude'])
    )

    if distance > max_radius:
        conn.close()
        return jsonify({
            "success": False, 
            "message": "Out of range",
            "distance_meters": round(distance),
            "required_radius": max_radius
        }), 403

    # Record Attendance
    student_id = session['user_id']
    record_id = str(uuid.uuid4())
    
    try:
        cursor.execute(
            "INSERT INTO attendance_records (id, session_id, student_id, distance_meters, status) VALUES (?, ?, ?, ?, 'PRESENT')",
            (record_id, att_session['id'], student_id, distance)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Attendance already marked for this session"}), 400
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "message": "Attendance marked successfully",
        "distance_meters": round(distance)
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
