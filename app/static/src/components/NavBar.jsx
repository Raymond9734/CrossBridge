import React, { useState } from 'react';
import { User, Bell, Menu } from 'lucide-react';
import { usePage, router } from '@inertiajs/react';

// Navbar Component
const Navbar = ({ currentUser, isSidebarOpen, setIsSidebarOpen }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileDropDown, setShowProfileDropDown] = useState(false);
  
  // Get notifications from backend
  const { notifications = { unread_count: 0, items: [] } } = usePage().props;
  
  const handleLogout = () => {
    router.post('/logout/');
  };
  
  // Close dropdowns when clicking outside
  const handleClickOutside = () => {
    setShowNotifications(false);
    setShowProfileDropDown(false);
  };
  
  return (
    <>
      {/* Backdrop to close dropdowns when clicking outside */}
      {(showNotifications || showProfileDropDown) && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={handleClickOutside}
        />
      )}
      
      <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="lg:hidden p-2 rounded-md hover:bg-gray-100 mr-3"
            >
              <Menu className="w-5 h-5" />
            </button>
            <h2 className="text-lg font-semibold text-gray-900">
              Welcome back, {currentUser?.name || 'User'}
            </h2>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Notifications Dropdown */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  setShowProfileDropDown(false); // Close profile dropdown
                }}
                className="p-2 rounded-full hover:bg-gray-100 relative"
              >
                <Bell className="w-5 h-5 text-gray-600" />
                {notifications.unread_count > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {notifications.unread_count > 9 ? '9+' : notifications.unread_count}
                  </span>
                )}
              </button>
              
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="font-semibold text-gray-900">
                      Notifications ({notifications.unread_count})
                    </h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.items.length > 0 ? (
                      notifications.items.map(notification => (
                        <div key={notification.id} className="p-4 hover:bg-gray-50 border-b border-gray-100">
                          <p className="font-medium text-sm">{notification.title}</p>
                          <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(notification.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        No notifications
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            {/* Profile Dropdown */}
            <div className="relative">
              <button
                onClick={() => {
                  setShowProfileDropDown(!showProfileDropDown);
                  setShowNotifications(false); // Close notifications dropdown
                }}
                className="flex items-center cursor-pointer hover:bg-gray-50 rounded-lg p-2 transition-colors"
              >
                <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                  <div className="ml-3 hidden sm:block">
                  <p className="text-xs text-gray-600 capitalize">{currentUser?.role || 'patient'}</p>           
                  <p className="text-sm font-medium text-gray-900">{currentUser?.name || 'User'}</p>
                </div>
              </button>
              
              {/* Profile Dropdown Menu */}
              {showProfileDropDown && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="py-1">
                    <button
                      onClick={() => {
                        handleLogout();
                        setShowProfileDropDown(false);
                      }}
                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                    >
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>
    </>
  );
};

export default Navbar;