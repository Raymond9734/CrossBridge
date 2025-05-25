import React, { useState, useEffect } from 'react';
import { User, Bell, Menu, RefreshCw } from 'lucide-react';
import { usePage, router } from '@inertiajs/react';

// Navbar Component
const Navbar = ({ currentUser, isSidebarOpen, setIsSidebarOpen }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileDropDown, setShowProfileDropDown] = useState(false);
  const [notifications, setNotifications] = useState({ unread_count: 0, items: [] });
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(false);
  
  // API utility function
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

  // Fetch notifications from API
  const fetchNotifications = async () => {
    setIsLoadingNotifications(true);
    try {
      const response = await apiCall('/api/v1/notifications/recent/?limit=10');
      
      if (response.success) {
        setNotifications({
          unread_count: response.notifications.filter(n => !n.is_read).length,
          items: response.notifications || []
        });
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
      // Keep existing notifications on error
    } finally {
      setIsLoadingNotifications(false);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await apiCall(`/api/v1/notifications/${notificationId}/mark_read/`, {
        method: 'POST'
      });
      
      // Update local state
      setNotifications(prev => ({
        unread_count: Math.max(0, prev.unread_count - 1),
        items: prev.items.map(item => 
          item.id === notificationId ? { ...item, is_read: true } : item
        )
      }));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      await apiCall('/api/v1/notifications/mark_all_read/', {
        method: 'POST'
      });
      
      // Update local state
      setNotifications(prev => ({
        unread_count: 0,
        items: prev.items.map(item => ({ ...item, is_read: true }))
      }));
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
    }
  };

  // Fetch notifications on mount and when dropdown opens
  useEffect(() => {
    fetchNotifications();
  }, []);

  useEffect(() => {
    if (showNotifications) {
      fetchNotifications();
    }
  }, [showNotifications]);
  
  const handleLogout = () => {
    router.post('/logout/');
  };
  
  // Close dropdowns when clicking outside
  const handleClickOutside = () => {
    setShowNotifications(false);
    setShowProfileDropDown(false);
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
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
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900">
                        Notifications ({notifications.unread_count})
                      </h3>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={fetchNotifications}
                          className="p-1 hover:bg-gray-100 rounded"
                          disabled={isLoadingNotifications}
                        >
                          <RefreshCw className={`w-4 h-4 text-gray-500 ${isLoadingNotifications ? 'animate-spin' : ''}`} />
                        </button>
                        {notifications.unread_count > 0 && (
                          <button
                            onClick={markAllAsRead}
                            className="text-xs text-teal-600 hover:text-teal-700 font-medium"
                          >
                            Mark all read
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {isLoadingNotifications && notifications.items.length === 0 ? (
                      <div className="p-4 text-center text-gray-500">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto mb-2"></div>
                        Loading notifications...
                      </div>
                    ) : notifications.items.length > 0 ? (
                      notifications.items.map(notification => (
                        <div 
                          key={notification.id} 
                          className={`p-4 hover:bg-gray-50 border-b border-gray-100 cursor-pointer transition-colors ${
                            !notification.is_read ? 'bg-blue-50' : ''
                          }`}
                          onClick={() => handleNotificationClick(notification)}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className={`text-sm ${!notification.is_read ? 'font-semibold' : 'font-medium'}`}>
                                {notification.title}
                              </p>
                              <p className="text-xs text-gray-600 mt-1">{notification.message}</p>
                              <p className="text-xs text-gray-400 mt-1">
                                {new Date(notification.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            {!notification.is_read && (
                              <div className="w-2 h-2 bg-blue-500 rounded-full mt-1 ml-2"></div>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-center text-gray-500">
                        <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
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