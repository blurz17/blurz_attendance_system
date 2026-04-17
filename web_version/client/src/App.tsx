import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import LoginPage from '@/pages/LoginPage';
import ActivatePage from '@/pages/ActivatePage';
import IntroPage from '@/pages/IntroPage';
import ProtectedRoute from '@/components/ProtectedRoute';
import ClientLayout from '@/components/layout/ClientLayout';
import StudentDashboard from '@/pages/student/Dashboard';
import AttendanceRecords from '@/pages/student/AttendanceRecords';
import QuizCenter from '@/pages/student/QuizCenter';
import InstructorDashboard from '@/pages/instructor/Dashboard';
import ScanQR from '@/pages/student/ScanQR';
import QuizSubmissions from '@/pages/instructor/QuizSubmissions';
import QRGeneration from '@/pages/instructor/QRGeneration';
import CreateQuiz from '@/pages/instructor/CreateQuiz';
import AttendanceHistory from '@/pages/instructor/AttendanceHistory';
import { useAuth } from '@/context/AuthContext';

const DashboardRouter = () => {
  const { user } = useAuth();
  if (user?.role === 'student') {
    return <StudentDashboard />;
  }
  return <InstructorDashboard />;
};

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider defaultTheme="dark">
        <AuthProvider>
          <Routes>
            {/* Public */}
            <Route path="/intro" element={<IntroPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/activate/:token" element={<ActivatePage />} />

            {/* Protected Client Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <ClientLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<DashboardRouter />} />

              {/* Student specific */}
              <Route path="/scan" element={<ScanQR />} />
              <Route path="/attendance" element={<AttendanceRecords />} />
              <Route path="/quizzes" element={<QuizCenter />} />

              {/* Instructor specific */}
              <Route path="/instructor/attendance" element={<QRGeneration />} />
              <Route path="/instructor/attendance/:courseId" element={<AttendanceHistory />} />
              <Route path="/instructor/quizzes" element={<CreateQuiz />} />
              <Route path="/instructor/quizzes/:quizId/submissions" element={<QuizSubmissions />} />

              {/* Other client routes will go here */}
            </Route>

            {/* Unauthorized */}
            <Route path="/unauthorized" element={
              <div className="min-h-screen bg-navy-950 text-white flex items-center justify-center p-8 text-center">
                <div>
                  <h1 className="text-4xl font-bold mb-4">Unauthorized</h1>
                  <p className="text-navy-400">You don't have permission to access this page.</p>
                </div>
              </div>
            } />
          </Routes>

          {/* Global Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              classNames: {
                toast: 'bg-navy-900 border border-white/10 shadow-lg rounded-xl',
                title: 'text-white font-medium',
                description: 'text-navy-300',
              },
            }}
            richColors
            closeButton
          />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
