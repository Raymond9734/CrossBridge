import React, { useState } from 'react';
import { usePage, router } from '@inertiajs/react';

// Profile Management Component
const ProfileManagement = ({ currentUser, showToast }) => {
  // Get profile data from backend
  const { profile = {} } = usePage().props;
  
  const [formData, setFormData] = useState({
    firstName: profile.firstName || currentUser?.first_name || '',
    lastName: profile.lastName || currentUser?.last_name || '',
    email: profile.email || currentUser?.email || '',
    phone: profile.phone || '',
    address: profile.address || '',
    emergencyContact: profile.emergencyContact || '',
    medicalHistory: profile.medicalHistory || ''
  });


  
  const [isLoading, setIsLoading] = useState(false);
  
  const handleSubmit = () => {
    setIsLoading(true);
    
    // Use Inertia.js to post to Django backend
    router.post('/profile/', formData, {
      onSuccess: () => {
        showToast('Profile updated successfully!', 'success');
      },
      onError: (errors) => {
        console.error('Profile update errors:', errors);
        showToast('Failed to update profile', 'error');
      },
      onFinish: () => {
        setIsLoading(false);
      }
    });
  };
  
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Profile Management</h2>
        <p className="text-sm text-gray-600 mt-1">Update your personal information</p>
      </div>
      
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">First Name</label>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Last Name</label>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              disabled={isLoading}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              disabled={isLoading}
            />
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">Emergency Contact</label>
            <input
              type="tel"
              name="emergencyContact"
              value={formData.emergencyContact}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              disabled={isLoading}
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
          <textarea
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            rows={3}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            disabled={isLoading}
          />
        </div>
        
        {currentUser?.role === 'patient' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Medical History</label>
            <textarea
              name="medicalHistory"
              value={formData.medicalHistory}
              onChange={handleInputChange}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              placeholder="Any allergies, chronic conditions, medications, etc."
              disabled={isLoading}
            />
          </div>
        )}
        
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSubmit}
            className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Updating...' : 'Update Profile'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileManagement;