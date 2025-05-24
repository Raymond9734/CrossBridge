import React, { useState } from 'react';
import DoctorDashboard from '../components/dashboard/Doctor'
import PatientDashboard from '../components/dashboard/Patient'
import AppointmentsList from '../components/AppointmentList';
import ProfileManagement from '../components/ProfileManagement';
import Sidebar from '../components/SideBar';
import Navbar from '../components/NavBar';
import Toast from '../components/ToastNotification';
import mockData from '../MockData/Data'; // Assuming you have a mockData file for demo purposes

// Main Healthcare App Component
const HealthcareApp = () => {
  const [currentUser, setCurrentUser] = useState(mockData.user);
  const [activeView, setActiveView] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ isVisible: false, message: '', type: 'info' });
  
  const showToast = (message, type = 'info') => {
    setToast({ isVisible: true, message, type });
  };
  
  const hideToast = () => {
    setToast({ ...toast, isVisible: false });
  };
  
  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return currentUser?.role === 'doctor' 
          ? <DoctorDashboard showToast={showToast} />
          : <PatientDashboard showToast={showToast} />;
      case 'appointments':
        return <AppointmentsList userRole={currentUser?.role} showToast={showToast} />;
      case 'book-appointment':
        return <PatientDashboard showToast={showToast} />;
      case 'profile':
        return <ProfileManagement currentUser={currentUser} showToast={showToast} />;
      case 'medical-records':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Medical Records</h2>
            <p className="text-gray-600">Medical records viewer would be implemented here with proper security and permission checks.</p>
          </div>
        );
      case 'schedule':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Schedule Management</h2>
            <p className="text-gray-600">Doctor schedule management interface would be implemented here.</p>
          </div>
        );
      case 'patients':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Patient Management</h2>
            <p className="text-gray-600">Patient list and management interface would be implemented here.</p>
          </div>
        );
      default:
        return <PatientDashboard showToast={showToast} />;
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50  lg:flex">
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