import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ProfessorDashboard from './components/ProfessorDashboard';
import StudentCheckIn from './components/StudentCheckIn';

function App() {
  return (
    <Router>
      <div className="min-h-screen p-4 flex flex-col items-center justify-center">
        <Routes>
          <Route path="/" element={
            <div className="glass-panel p-8 max-w-md w-full text-center space-y-6">
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
                Proximity Attendance
              </h1>
              <p className="text-gray-400">Select your role to continue</p>
              
              <div className="flex flex-col gap-4 mt-8">
                <Link to="/professor" className="primary-btn">
                  I am a Professor
                </Link>
                <Link to="/student" className="bg-gray-800 hover:bg-gray-700 text-white font-semibold py-3 px-6 rounded-xl transition-all shadow-lg">
                  I am a Student
                </Link>
              </div>
            </div>
          } />
          <Route path="/professor" element={<ProfessorDashboard />} />
          <Route path="/student" element={<StudentCheckIn />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
