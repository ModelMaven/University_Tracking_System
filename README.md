# 📍 Proximity-Based Student Attendance System

A modern, web-based student attendance system that uses **GPS proximity** and **OTP verification** to ensure students are physically present in class before marking attendance.

## ✨ Features

### 👨‍💼 Admin Hub (Hub-and-Spoke Architecture)
- **Centralized Dashboard** with 5 dedicated management tiles
- **Student Management** — View, edit roles, set passwords manually, assign emergency admin contact
- **Professor Management** — Full CRUD with role editing and password management
- **Admin Management** — Invite & manage System Administrators
- **Course Management** — Create courses, assign professors, multi-enroll students
- **Master Attendance Reports** — Aggregated attendance log across all courses

### 🔐 Authentication & Security
- **Email Invitation System** — Admins invite users; no plain-text passwords ever stored in CSV files
- **Forgot Password Flow** — Secure token-based password reset (24-hour expiry)
- **Manual Admin Password Reset** — Admins can set passwords directly if a user didn't receive their email
- **Multi-Role Dual Access** — A user can hold `ADMIN`, `PROFESSOR`, and `STUDENT` roles simultaneously
- **Role Selection Portal** — Users with multiple roles choose which dashboard to access at login

### 👨‍🏫 Professor Dashboard
- Start attendance sessions with GPS anchor point + 6-digit OTP
- View live session status and enrolled students

### 🎓 Student Dashboard
- Enter OTP to check in — GPS verifies you are within the required radius
- View enrolled courses and upcoming assignments
- **Emergency Admin Contact** card — assigned and controlled by your admin

### 📊 Bulk Management
- Download a sample CSV template (`First Name, Last Name, Email`)
- Upload CSV to bulk-create and auto-invite users via email

## 🚀 Getting Started

### Prerequisites
- Python 3.9+

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/attendance-system.git
cd attendance-system

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r backend_python/requirements.txt

# 4. Run the server
python backend_python/app.py
```

The app will start at **http://127.0.0.1:5000**

### 🧪 Default Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@system.com` | `admin123` |
| Professor | `smith@test.com` | `prof123` |
| Student | `jane@test.com` | `student123` |

> **Note:** The SQLite database (`attendance.db`) is auto-generated on first run and is excluded from version control.

## 🗂️ Project Structure

```
attendance/
├── backend_python/
│   ├── app.py              # Flask app — all routes and logic
│   ├── db.py               # Database schema and initialization
│   ├── geo.py              # Haversine distance calculation
│   ├── requirements.txt    # Python dependencies
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html
│       ├── login.html
│       ├── forgot_password.html
│       ├── reset_password.html
│       ├── admin_hub.html
│       ├── admin_students.html
│       ├── admin_professors.html
│       ├── admin_admins.html
│       ├── admin_courses.html
│       ├── admin_reports.html
│       ├── professor.html
│       ├── student.html
│       └── select_role.html
└── frontend/               # (Legacy/alternative frontend assets)
```

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **Frontend:** HTML, Jinja2, Tailwind CSS (CDN)
- **Auth:** Werkzeug password hashing, session-based auth
- **Geo:** Native Python Haversine formula (no external geo libraries needed)

## 📧 Email System (MVP Mode)
During local development, all emails (invitations, password resets) are **printed to the terminal** in a clearly marked block. In production, replace the mock email section in `app.py` with a real SMTP provider (e.g., SendGrid, Mailgun, or Gmail SMTP).

## 📄 License
MIT
