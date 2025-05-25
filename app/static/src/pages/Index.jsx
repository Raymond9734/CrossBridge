import React, { useState, useEffect } from 'react';
import { usePage } from '@inertiajs/react';
import DoctorDashboard from '../components/dashboard/Doctor';
import PatientDashboard from '../components/dashboard/Patient';
import AppointmentsList from '../components/AppointmentList';
import ProfileManagement from '../components/ProfileManagement';
import MedicalRecords from '../components/MedicalRecord';
import ScheduleManagement from '../components/ScheduleManagement';
import PatientManagement from '../components/PatientManagement';
import Sidebar from '../components/SideBar';
import Navbar from '../components/NavBar';
import Toast from '../components/ToastNotification';
import { AlertTriangle, Home, ArrowLeft } from 'lucide-react';

// API utility functions
const apiCall = async (url, options = {}) => {
  const getCSRFToken = () => {
    const metaTag = document.querySelector('meta[name=csrf-token]');
    const tokenFromMeta = metaTag?.getAttribute('content') || metaTag?.textContent || '';
    
    const getCookie = (name) => {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    };
    
    return tokenFromMeta || getCookie('csrftoken') || '';
  };

  const csrfToken = getCSRFToken();
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
      'X-CSRF-Token': csrfToken,
    }
  };

  const response = await fetch(url, { ...defaultOptions, ...options });
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.error || 'API request failed');
  }
  
  return data;
};

// 404 Page Component
const NotFoundPage = () => {
  const handleGoHome = () => {
    window.location.href = '/login/';
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="flex justify-center mb-6">
            <div className="bg-red-100 p-4 rounded-full">
              <AlertTriangle className="w-12 h-12 text-red-600" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Access Denied</h1>
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Invalid User Role</h2>
          <p className="text-gray-600 mb-6">
            Your account doesn't have the proper permissions to access this healthcare system. 
            Please contact your administrator or sign in with a valid doctor or patient account.
          </p>
        </div>
        
        <div className="space-y-3">
          <button
            onClick={handleGoHome}
            className="w-full bg-teal-600 text-white px-6 py-3 rounded-lg hover:bg-teal-700 transition-colors flex items-center justify-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Login
          </button>
          
          <button
            onClick={() => window.location.href = '/register/'}
            className="w-full bg-white text-teal-600 px-6 py-3 rounded-lg border border-teal-600 hover:bg-teal-50 transition-colors flex items-center justify-center gap-2"
          >
            <Home className="w-4 h-4" />
            Create Account
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Healthcare App Component
const HealthcareApp = () => {
  const props = usePage().props;
  
  const [activeView, setActiveView] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ isVisible: false, message: '', type: 'info' });
  
  // State for API data
  const [dashboardData, setDashboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(props.user || null);
  
  // Validate user role
  const isValidRole = currentUser?.role && ['doctor', 'patient'].includes(currentUser.role);
  
  if (!isValidRole) {
    return <NotFoundPage />;
  }
  
  // Fetch dashboard data on component mount and when user changes
  useEffect(() => {
    if (currentUser) {
      fetchDashboardData();
    }
  }, [currentUser?.id]);

  const fetchDashboardData = async () => {
    try {
      setIsLoading(true);
      const response = await apiCall('/api/v1/dashboard/data/');
      
      if (response.success) {
        setDashboardData(response.data);
        // Update current user with latest data
        if (response.data.user) {
          setCurrentUser(response.data.user);
        }
      } else {
        showToast('Failed to load dashboard data', 'error');
      }
    } catch (error) {
      console.error('Dashboard data fetch error:', error);
      showToast('Failed to load dashboard data', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const showToast = (message, type = 'info') => {
    setToast({ isVisible: true, message, type });
  };
  
  const hideToast = () => {
    setToast({ ...toast, isVisible: false });
  };
  
  const renderActiveView = () => {
    if (isLoading && !dashboardData) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
          <span className="ml-3 text-gray-600">Loading...</span>
        </div>
      );
    }

    switch (activeView) {
      case 'dashboard':
        return currentUser?.role === 'doctor' 
          ? <DoctorDashboard 
              showToast={showToast} 
              dashboardData={dashboardData}
              refreshData={fetchDashboardData}
            />
          : <PatientDashboard 
              showToast={showToast} 
              dashboardData={dashboardData}
              refreshData={fetchDashboardData}
            />;
            
      case 'appointments':
        return <AppointmentsList 
          userRole={currentUser?.role} 
          showToast={showToast} 
        />;
        
      case 'book-appointment':
        return <PatientDashboard 
          showToast={showToast} 
          dashboardData={dashboardData}
          refreshData={fetchDashboardData}
          autoOpenBooking={true}
        />;
        
      case 'profile':
        return <ProfileManagement 
          currentUser={currentUser} 
          showToast={showToast}
          onProfileUpdate={fetchDashboardData}
        />;
        
      case 'medical-records':
        return <MedicalRecords showToast={showToast} />;
        
      case 'schedule':
        return <ScheduleManagement showToast={showToast} />;
        
      case 'patients':
        return <PatientManagement showToast={showToast} />;
        
      default:
        return currentUser?.role === 'doctor' 
          ? <DoctorDashboard 
              showToast={showToast} 
              dashboardData={dashboardData}
              refreshData={fetchDashboardData}
            />
          : <PatientDashboard 
              showToast={showToast} 
              dashboardData={dashboardData}
              refreshData={fetchDashboardData}
            />;
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50 lg:flex">
      {/* Toast Notifications */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
      
      {/* Sidebar */}
      <Sidebar
        currentUser={currentUser}
        activeView={activeView}
        setActiveView={setActiveView}
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
      />
      
      {/* Main Content */}
      <div className="flex-1">
        {/* Navbar */}
        <Navbar
          currentUser={currentUser}
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
          notifications={dashboardData?.notifications || { unread_count: 0, items: [] }}
        />
        
        {/* Page Content */}
        <main className="p-4 md:p-6">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
};

export default HealthcareApp;
