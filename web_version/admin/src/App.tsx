import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/context/AuthContext';
import { ThemeProvider } from '@/context/ThemeContext';
import AdminLayout from '@/components/layout/AdminLayout';
import ProtectedRoute from '@/components/layout/ProtectedRoute';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import UsersPage from '@/pages/UsersPage';
import DepartmentsPage from '@/pages/DepartmentsPage';
import SectionsPage from '@/pages/SectionsPage';
import CoursesPage from '@/pages/CoursesPage';

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Admin Routes */}
            <Route
              element={
                <ProtectedRoute>
                  <AdminLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<DashboardPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/departments" element={<DepartmentsPage />} />
              <Route path="/sections" element={<SectionsPage />} />
              <Route path="/courses" element={<CoursesPage />} />
            </Route>
          </Routes>

          {/* Global Toast Notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              classNames: {
                toast: 'bg-surface border border-border shadow-lg rounded-xl',
                title: 'text-text-primary font-medium',
                description: 'text-text-secondary',
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
