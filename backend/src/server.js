const express = require('express');
const cors = require('cors');
require('dotenv').config();

const { startAttendance, verifyAttendance } = require('./controllers/attendanceController');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.post('/api/attendance/start', startAttendance);
app.post('/api/attendance/verify', verifyAttendance);

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date() });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
