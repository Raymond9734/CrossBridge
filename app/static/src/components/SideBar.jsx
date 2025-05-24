
import React from 'react';
import { Calendar, Clock, User, Users, Bell, Settings,  Plus} from 'lucide-react';



// Sidebar Component
const Sidebar = ({ currentUser, activeView, setActiveView, isSidebarOpen, setIsSidebarOpen }) => {
    const patientNavItems = [
      { id: 'dashboard', label: 'Dashboard', icon: Calendar },
      { id: 'appointments', label: 'My Appointments', icon: Clock },
      { id: 'book-appointment', label: 'Book Appointment', icon: Plus },
      { id: 'medical-records', label: 'Medical Records', icon: User },
      { id: 'profile', label: 'Profile', icon: Settings }
    ];
  
    const doctorNavItems = [
      { id: 'dashboard', label: 'Dashboard', icon: Calendar },
      { id: 'schedule', label: 'My Schedule', icon: Clock },
      { id: 'patients', label: 'Patients', icon: Users },
      { id: 'appointments', label: 'Appointments', icon: Calendar },
      { id: 'profile', label: 'Profile', icon: Settings }
    ];
  
    const navItems = currentUser?.role === 'doctor' ? doctorNavItems : patientNavItems;
  
    return (
      <>
        {/* Mobile Overlay */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" 
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
        
        {/* Sidebar */}
        <div className={`
        fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-50
        transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
        transition-transform duration-300 ease-in-out
        lg:relative lg:translate-x-0 lg:flex lg:flex-col lg:w-64 lg:min-h-screen
      `}>
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-teal-600">CareBridge</h1>
            <p className="text-sm text-gray-600 mt-1">Healthcare Management</p>
          </div>
          
          <nav className="mt-6">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveView(item.id);
                    setIsSidebarOpen(false);
                  }}
                  className={`w-full flex items-center px-6 py-3 text-left hover:bg-teal-50 transition-colors ${
                    activeView === item.id ? 'bg-teal-50 text-teal-600 border-r-2 border-teal-600' : 'text-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </>
    );
};
  
export default Sidebar;