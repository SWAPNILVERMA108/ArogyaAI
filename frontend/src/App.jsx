import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import { ROLES } from './constants'
import AppLayout from './layouts/AppLayout'
import PublicLayout from './layouts/PublicLayout'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import EmergencyPage from './pages/EmergencyPage'
import HealthTipsPage from './pages/HealthTipsPage'
import HospitalsPage from './pages/HospitalsPage'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import MedicinesPage from './pages/MedicinesPage'
import NotFoundPage from './pages/NotFoundPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'
import ReportsPage from './pages/ReportsPage'
import AdminDashboardPage from './pages/admin/AdminDashboardPage'
import AdminHospitalsPage from './pages/admin/AdminHospitalsPage'
import AdminUsersPage from './pages/admin/AdminUsersPage'
import DoctorDashboardPage from './pages/doctor/DoctorDashboardPage'
import DoctorPatientsPage from './pages/doctor/DoctorPatientsPage'

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/hospitals" element={<HospitalsPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute roles={[ROLES.PATIENT]} />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/medicines" element={<MedicinesPage />} />
          <Route path="/health-tips" element={<HealthTipsPage />} />
          <Route path="/emergency" element={<EmergencyPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute roles={[ROLES.DOCTOR]} />}>
        <Route element={<AppLayout />}>
          <Route path="/doctor/dashboard" element={<DoctorDashboardPage />} />
          <Route path="/doctor/patients" element={<DoctorPatientsPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute roles={[ROLES.ADMIN]} />}>
        <Route element={<AppLayout />}>
          <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/hospitals" element={<AdminHospitalsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
