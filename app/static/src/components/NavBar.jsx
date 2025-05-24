import React, { useState } from 'react';
import { User,  Bell,  Menu} from 'lucide-react';



// Navbar Component
const Navbar = ({ currentUser, isSidebarOpen, setIsSidebarOpen }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 mr-3"
          >
            <Menu className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900">Welcome back, {currentUser?.name}</h2>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-full hover:bg-gray-100 relative"
            >
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                3
              </span>
            </button>
            
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  <div className="p-4 hover:bg-gray-50 border-b border-gray-100">
                    <p className="font-medium text-sm">New appointment request</p>
                    <p className="text-xs text-gray-600 mt-1">John Smith requested an appointment for tomorrow</p>
                  </div>
                  <div className="p-4 hover:bg-gray-50 border-b border-gray-100">
                    <p className="font-medium text-sm">Appointment confirmed</p>
                    <p className="text-xs text-gray-600 mt-1">Your appointment with Dr. Johnson is confirmed</p>
                  </div>
                  <div className="p-4 hover:bg-gray-50">
                    <p className="font-medium text-sm">Medical records updated</p>
                    <p className="text-xs text-gray-600 mt-1">New test results are available</p>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center">
            <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="ml-3 hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{currentUser?.name}</p>
              <p className="text-xs text-gray-600 capitalize">{currentUser?.role}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
