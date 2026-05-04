import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'

// Public pages
import Home from './pages/Home'
import JobSearch from './pages/JobSearch'
import JobDetail from './pages/JobDetail'
import CompanyProfile from './pages/CompanyProfile'
import CareerAdvice from './pages/CareerAdvice'
import CareerSolutions from './pages/CareerSolutions'
import Prep from './pages/Prep'
import Learn from './pages/Learn'
import Login from './pages/Login'
import Register from './pages/Register'
import DashboardLayout from './components/layout/DashboardLayout'

// Seeker pages
import SeekerDashboard from './pages/seeker/Dashboard'
import AppliedJobs from './pages/seeker/AppliedJobs'
import SavedJobs from './pages/seeker/SavedJobs'
import SeekerProfile from './pages/seeker/Profile'
import Resume from './pages/seeker/Resume'
import JobAlerts from './pages/seeker/JobAlerts'

// Employer pages
import EmployerDashboard from './pages/employer/Dashboard'
import PostJob from './pages/employer/PostJob'
import MyJobs from './pages/employer/MyJobs'
import Applicants from './pages/employer/Applicants'

import Spinner from './components/ui/Spinner'

function ComingSoon({ title }: { title: string }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-[#f5f5f5]">
      <h1 className="text-3xl font-bold text-[#1a1a2e]">{title}</h1>
      <p className="text-gray-500">This page is coming soon. Stay tuned!</p>
    </div>
  )
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

function ProtectedRoute({ children, role }: { children: React.ReactNode; role?: 'SEEKER' | 'EMPLOYER' }) {
  const { isAuthenticated, user, isLoading } = useAuth()
  if (isLoading) return <Spinner fullPage />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (role && user?.role !== role) {
    return <Navigate to={user?.role === 'EMPLOYER' ? '/employer/dashboard' : '/dashboard'} replace />
  }
  return <>{children}</>
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user, isLoading } = useAuth()
  if (isLoading) return <Spinner fullPage />
  if (isAuthenticated) {
    return <Navigate to={user?.role === 'EMPLOYER' ? '/employer/dashboard' : '/dashboard'} replace />
  }
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Home />} />
      <Route path="/jobs" element={<JobSearch />} />
      <Route path="/jobs/:id" element={<JobDetail />} />
      <Route path="/company/:id" element={<CompanyProfile />} />
      <Route path="/career-advice" element={<CareerAdvice />} />
      <Route path="/career-solutions" element={<CareerSolutions />} />
      <Route path="/prep" element={<Prep />} />
      <Route path="/learn" element={<Learn />} />
      <Route path="/salary-insights" element={<ComingSoon title="Salary Insights" />} />

      {/* Guest only */}
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />

      {/* Seeker routes */}
      <Route element={<ProtectedRoute role="SEEKER"><DashboardLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<SeekerDashboard />} />
        <Route path="/dashboard/applied" element={<AppliedJobs />} />
        <Route path="/dashboard/saved" element={<SavedJobs />} />
        <Route path="/dashboard/profile" element={<SeekerProfile />} />
        <Route path="/dashboard/resume" element={<Resume />} />
        <Route path="/dashboard/alerts" element={<JobAlerts />} />
      </Route>

      {/* Employer routes */}
      <Route element={<ProtectedRoute role="EMPLOYER"><DashboardLayout /></ProtectedRoute>}>
        <Route path="/employer/dashboard" element={<EmployerDashboard />} />
        <Route path="/employer/post-job" element={<PostJob />} />
        <Route path="/employer/jobs" element={<MyJobs />} />
        <Route path="/employer/jobs/:jobId/applicants" element={<Applicants />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <AppRoutes />
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 3000,
              style: { background: '#333', color: '#fff' },
              success: { style: { background: '#28a745', color: '#fff' } },
              error: { style: { background: '#dc3545', color: '#fff' } },
            }}
          />
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
