const db = require('../db');
const { calculateDistance } = require('../utils/geo');
const crypto = require('crypto');

// Generate a random 6-digit OTP
const generateOTP = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
};

const startAttendance = async (req, res) => {
    try {
        const { timetable_id, latitude, longitude } = req.body;
        
        // Mock Professor ID for MVP (Would come from JWT auth)
        const professor_id = req.user?.id || 'd3b07384-d9a7-4780-9999-5f212278061e';

        const otp = generateOTP();
        
        // Session valid for 15 minutes
        const expires_at = new Date();
        expires_at.setMinutes(expires_at.getMinutes() + 15);

        const result = await db.query(
            `INSERT INTO attendance_sessions 
            (timetable_id, professor_id, otp, anchor_latitude, anchor_longitude, expires_at) 
            VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, otp, expires_at`,
            [timetable_id, professor_id, otp, latitude, longitude, expires_at]
        );

        res.status(201).json({
            success: true,
            data: result.rows[0],
            message: 'Attendance session started successfully'
        });
    } catch (error) {
        console.error('Error starting attendance:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};

const verifyAttendance = async (req, res) => {
    try {
        const { otp, latitude, longitude } = req.body;
        
        // Mock Student ID for MVP (Would come from JWT auth)
        const student_id = req.user?.id || 'a1b2c3d4-e5f6-7890-1234-56789abcdef0';

        // 1. Validate OTP and check if session is active
        const sessionResult = await db.query(
            `SELECT id, anchor_latitude, anchor_longitude, expires_at 
             FROM attendance_sessions 
             WHERE otp = $1 
             ORDER BY created_at DESC LIMIT 1`,
            [otp]
        );

        if (sessionResult.rows.length === 0) {
            return res.status(400).json({ success: false, message: 'Invalid OTP' });
        }

        const session = sessionResult.rows[0];

        if (new Date() > new Date(session.expires_at)) {
            return res.status(400).json({ success: false, message: 'OTP has expired' });
        }

        // 2. Fetch required radius from settings
        const settingsResult = await db.query(
            `SELECT value FROM settings WHERE key = 'attendance_radius_meters'`
        );
        const maxRadius = parseFloat(settingsResult.rows[0]?.value || '20');

        // 3. Calculate Distance
        const distance = calculateDistance(
            parseFloat(latitude), 
            parseFloat(longitude), 
            parseFloat(session.anchor_latitude), 
            parseFloat(session.anchor_longitude)
        );

        if (distance > maxRadius) {
            return res.status(403).json({ 
                success: false, 
                message: 'Out of range', 
                distance_meters: Math.round(distance),
                required_radius: maxRadius
            });
        }

        // 4. Record Attendance
        await db.query(
            `INSERT INTO attendance_records (session_id, student_id, distance_meters, status) 
             VALUES ($1, $2, $3, 'PRESENT')`,
            [session.id, student_id, distance]
        );

        res.status(200).json({ 
            success: true, 
            message: 'Attendance marked successfully',
            distance_meters: Math.round(distance)
        });

    } catch (error) {
        if (error.code === '23505') { // Unique violation in PG
            return res.status(400).json({ success: false, message: 'Attendance already marked for this session' });
        }
        console.error('Error verifying attendance:', error);
        res.status(500).json({ success: false, message: 'Internal server error' });
    }
};

module.exports = {
    startAttendance,
    verifyAttendance
};
