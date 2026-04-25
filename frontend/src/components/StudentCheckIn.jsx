import { useState } from 'react';
import { MapPin, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { Link } from 'react-router-dom';

export default function StudentCheckIn() {
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ type: 'idle', message: '' }); // idle, success, error

  const handleCheckIn = (e) => {
    e.preventDefault();
    if (otp.length !== 6) {
      setStatus({ type: 'error', message: 'Please enter a valid 6-digit OTP' });
      return;
    }

    setLoading(true);
    setStatus({ type: 'idle', message: '' });

    if (!navigator.geolocation) {
      setStatus({ type: 'error', message: 'Geolocation is not supported by your browser.' });
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          
          const response = await axios.post('/api/attendance/verify', {
            otp,
            latitude,
            longitude
          });

          setStatus({ 
            type: 'success', 
            message: `Success! Checked in from ${response.data.distance_meters}m away.`
          });
        } catch (err) {
          const errorMsg = err.response?.data?.message || 'Failed to verify attendance.';
          const distance = err.response?.data?.distance_meters;
          const required = err.response?.data?.required_radius;
          
          let fullMessage = errorMsg;
          if (distance && required) {
            fullMessage += ` (You are ${distance}m away, max is ${required}m)`;
          }

          setStatus({ type: 'error', message: fullMessage });
        } finally {
          setLoading(false);
        }
      },
      (err) => {
        setStatus({ type: 'error', message: 'Location access denied. We need your location to verify attendance.' });
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  return (
    <div className="w-full max-w-lg glass-panel p-8">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-bold">Student Check-In</h2>
        <Link to="/" className="text-sm text-gray-400 hover:text-white">Back</Link>
      </div>

      {status.type === 'success' ? (
        <div className="text-center space-y-6 animate-in zoom-in duration-300 py-8">
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-green-500/20 text-green-500 mb-4">
            <CheckCircle2 size={48} />
          </div>
          <h3 className="text-2xl font-bold text-white">Attendance Marked!</h3>
          <p className="text-green-400">{status.message}</p>
          <button onClick={() => setStatus({type: 'idle', message: ''})} className="text-gray-400 hover:text-white underline mt-8 block w-full">
            Check into another class
          </button>
        </div>
      ) : (
        <form onSubmit={handleCheckIn} className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300">Enter Class OTP</label>
            <input 
              type="text" 
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/[^0-9]/g, ''))}
              placeholder="000000"
              className="input-field text-center text-3xl tracking-[1em] font-mono h-20"
              required
            />
          </div>

          <button 
            type="submit"
            disabled={loading || otp.length !== 6}
            className="w-full primary-btn flex items-center justify-center gap-2 h-14 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                Verifying Location...
              </>
            ) : (
              <>
                <MapPin size={20} />
                Check In Now
              </>
            )}
          </button>

          {status.type === 'error' && (
            <div className="flex items-center gap-3 text-red-400 bg-red-400/10 p-4 rounded-xl border border-red-400/20 animate-in slide-in-from-top-2">
              <AlertCircle size={24} className="shrink-0" />
              <p className="text-sm">{status.message}</p>
            </div>
          )}
        </form>
      )}
    </div>
  );
}
