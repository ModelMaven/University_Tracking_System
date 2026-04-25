import { useState } from 'react';
import { MapPin, Users, Loader2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';

export default function ProfessorDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [session, setSession] = useState(null);

  const handleStartAttendance = () => {
    setLoading(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          
          // Call API to start session
          const response = await axios.post('/api/attendance/start', {
            timetable_id: '123e4567-e89b-12d3-a456-426614174000', // Mock timetable UUID
            latitude,
            longitude
          });

          setSession(response.data.data);
        } catch (err) {
          setError(err.response?.data?.message || 'Failed to start attendance session.');
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setError('Location access denied. We need your location to prevent proxy attendance.');
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  return (
    <div className="w-full max-w-lg glass-panel p-8">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold">Professor Dashboard</h2>
        <Link to="/" className="text-sm text-gray-400 hover:text-white">Back</Link>
      </div>

      {!session ? (
        <div className="space-y-6">
          <div className="bg-gray-800/50 p-4 rounded-xl border border-gray-700">
            <h3 className="font-semibold text-lg">CS 101: Data Structures</h3>
            <p className="text-sm text-gray-400">10:00 AM - 11:30 AM</p>
          </div>

          <button 
            onClick={handleStartAttendance} 
            disabled={loading}
            className="w-full primary-btn flex items-center justify-center gap-2 h-14"
          >
            {loading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <>
                <MapPin size={20} />
                Start Attendance
              </>
            )}
          </button>

          {error && (
            <div className="flex items-center gap-2 text-red-400 bg-red-400/10 p-4 rounded-xl border border-red-400/20">
              <AlertCircle size={20} />
              <p className="text-sm">{error}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="space-y-2">
            <p className="text-gray-400">Share this code with students</p>
            <div className="text-6xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400 py-4">
              {session.otp}
            </div>
          </div>
          
          <div className="bg-gray-800/50 p-6 rounded-xl border border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Users className="text-blue-400" size={24} />
              <div className="text-left">
                <p className="text-sm text-gray-400">Status</p>
                <p className="font-semibold text-green-400">Accepting Check-ins</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-400">Expires</p>
              <p className="font-mono">{new Date(session.expires_at).toLocaleTimeString()}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
