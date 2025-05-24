import React, { useState } from 'react';
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

// Main Healthcare App Component
const HealthcareApp = () => {
  // Get data from Django backend via Inertia.js
  // The Django backend sends all data as top-level props
  const props = usePage().props;
  
  const [activeView, setActiveView] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ isVisible: false, message: '', type: 'info' });
  
  // Get current user from props
  const currentUser = props.user;
  
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
          ? <DoctorDashboard 
              showToast={showToast} 
              dashboardData={{
                stats: props.stats,
                appointments: props.appointments,
                patients: props.patients
              }}
            />
          : <PatientDashboard 
              showToast={showToast} 
              dashboardData={{
                stats: props.stats,
                appointments: props.appointments,
                medical_records: props.medical_records
              }}
            />;
            
      case 'appointments':
        return <AppointmentsList userRole={currentUser?.role} showToast={showToast} />;
        
      case 'book-appointment':
        // For book appointment, we'll show the patient dashboard which has the booking modal
        return <PatientDashboard 
          showToast={showToast} 
          dashboardData={{
            stats: props.stats,
            appointments: props.appointments,
            medical_records: props.medical_records
          }}
        />;
        
      case 'profile':
        return <ProfileManagement currentUser={currentUser} showToast={showToast} />;
        
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
              dashboardData={{
                stats: props.stats,
                appointments: props.appointments,
                patients: props.patients
              }}
            />
          : <PatientDashboard 
              showToast={showToast} 
              dashboardData={{
                stats: props.stats,
                appointments: props.appointments,
                medical_records: props.medical_records
              }}
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
          notifications={props.notifications || { unread_count: 0, items: [] }}
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