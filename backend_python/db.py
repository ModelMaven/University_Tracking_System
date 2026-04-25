import sqlite3
import uuid
import datetime
import os
from werkzeug.security import generate_password_hash

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance.db')

def get_db():
    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users Table (RBAC + Auth)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        role TEXT NOT NULL,
        assigned_admin_id TEXT,
        FOREIGN KEY(assigned_admin_id) REFERENCES users(id)
    )
    ''')

    # 1.5 Password Reset Tokens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')

    # 2. Courses Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        professor_id TEXT,
        FOREIGN KEY(professor_id) REFERENCES users(id)
    )
    ''')

    # 3. Enrollments Table (Students in Courses)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enrollments (
        student_id TEXT,
        course_id TEXT,
        PRIMARY KEY(student_id, course_id),
        FOREIGN KEY(student_id) REFERENCES users(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    ''')

    # 4. Assignments Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS assignments (
        id TEXT PRIMARY KEY,
        course_id TEXT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    ''')

    # 5. Settings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    ''')
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('attendance_radius_meters', '20')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_host', '')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_port', '587')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_user', '')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_password', '')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_from_name', 'University Attendance System')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('smtp_from_email', '')")

    # 6. Attendance Sessions (Linked to Course)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        id TEXT PRIMARY KEY,
        course_id TEXT,
        professor_id TEXT,
        otp TEXT NOT NULL,
        anchor_latitude REAL NOT NULL,
        anchor_longitude REAL NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_id) REFERENCES courses(id),
        FOREIGN KEY(professor_id) REFERENCES users(id)
    )
    ''')

    # 7. Attendance Records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id TEXT PRIMARY KEY,
        session_id TEXT,
        student_id TEXT,
        distance_meters REAL NOT NULL,
        status TEXT DEFAULT 'PRESENT',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(session_id, student_id),
        FOREIGN KEY(session_id) REFERENCES attendance_sessions(id),
        FOREIGN KEY(student_id) REFERENCES users(id)
    )
    ''')

    # SEED INITIAL DATA
    admin_id = str(uuid.uuid4())
    prof_id = 'prof_1'
    student_id = 'student_1'
    
    admin_pass = generate_password_hash('admin123')
    prof_pass = generate_password_hash('prof123')
    student_pass = generate_password_hash('student123')

    # Initial Admin provided by Developer
    cursor.execute("INSERT OR IGNORE INTO users (id, first_name, last_name, email, password_hash, role) VALUES (?, 'System', 'Admin', 'admin@system.com', ?, 'ADMIN')", (admin_id, admin_pass))
    
    # Mock Prof and Student
    cursor.execute("INSERT OR IGNORE INTO users (id, first_name, last_name, email, password_hash, role) VALUES (?, 'Dr. John', 'Smith', 'smith@test.com', ?, 'PROFESSOR')", (prof_id, prof_pass))
    cursor.execute("INSERT OR IGNORE INTO users (id, first_name, last_name, email, password_hash, role, assigned_admin_id) VALUES (?, 'Jane', 'Doe', 'jane@test.com', ?, 'STUDENT', ?)", (student_id, student_pass, admin_id))

    # Mock Course
    course_id = 'course_1'
    cursor.execute("INSERT OR IGNORE INTO courses (id, name, professor_id) VALUES (?, 'CS 101: Data Structures', ?)", (course_id, prof_id))
    
    # Mock Enrollment
    cursor.execute("INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?, ?)", (student_id, course_id))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully with Phase 2 Schema.")
