import React, { useState, useEffect } from 'react';
import { Clock, Calendar, Plus, Edit, Trash2, Save, X } from 'lucide-react';
import { router, usePage } from '@inertiajs/react';

const ScheduleManagement = ({ showToast }) => {
  const [availability, setAvailability] = useState([]);
  const [editingSlot, setEditingSlot] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Get current availability from backend
  const { doctor_availability = [] } = usePage().props;
  
  useEffect(() => {
    setAvailability(doctor_availability);
  }, [doctor_availability]);

  const daysOfWeek = [
    { id: 0, name: 'Monday', short: 'Mon' },
    { id: 1, name: 'Tuesday', short: 'Tue' },
    { id: 2, name: 'Wednesday', short: 'Wed' },
    { id: 3, name: 'Thursday', short: 'Thu' },
    { id: 4, name: 'Friday', short: 'Fri' },
    { id: 5, name: 'Saturday', short: 'Sat' },
    { id: 6, name: 'Sunday', short: 'Sun' }
  ];

  const timeSlots = [
    '08:00', '08:30', '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30', '17:00', '17:30', '18:00', '18:30', '19:00', '19:30'
  ];

  const AddAvailabilityForm = ({ onClose, onSave }) => {
    const [formData, setFormData] = useState({
      day_of_week: '',
      start_time: '',
      end_time: '',
      is_available: true
    });
    const [errors, setErrors] = useState({});
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      const newErrors = {};
      
      if (!formData.day_of_week) newErrors.day_of_week = 'Please select a day';
      if (!formData.start_time) newErrors.start_time = 'Please select start time';
      if (!formData.end_time) newErrors.end_time = 'Please select end time';
      if (formData.start_time && formData.end_time && formData.start_time >= formData.end_time) {
        newErrors.end_time = 'End time must be after start time';
      }
      
      if (Object.keys(newErrors).length > 0) {
        setErrors(newErrors);
        return;
      }
      
      setSubmitting(true);
      
      try {
        const response = await fetch('/api/doctor-availability/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrf-token]')?.content || '',
          },
          body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
          showToast('Availability added successfully!', 'success');
          // Add the new availability to the state
          setAvailability(prev => [...prev, data.availability]);
          onClose();
        } else {
          setErrors(data.errors || { general: data.error || 'Failed to add availability' });
        }
      } catch (error) {
        console.error('Error adding availability:', error);
        setErrors({ general: 'Failed to add availability' });
      } finally {
        setSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Add Availability</h3>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {errors.general && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                {errors.general}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Day of Week</label>
              <select
                value={formData.day_of_week}
                onChange={(e) => setFormData({...formData, day_of_week: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
              >
                <option value="">Select a day</option>
                {daysOfWeek.map(day => (
                  <option key={day.id} value={day.id}>{day.name}</option>
                ))}
              </select>
              {errors.day_of_week && <p className="mt-1 text-sm text-red-600">{errors.day_of_week}</p>}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Start Time</label>
                <select
                  value={formData.start_time}
                  onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
                >
                  <option value="">Select time</option>
                  {timeSlots.map(time => (
                    <option key={time} value={time}>{time}</option>
                  ))}
                </select>
                {errors.start_time && <p className="mt-1 text-sm text-red-600">{errors.start_time}</p>}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">End Time</label>
                <select
                  value={formData.end_time}
                  onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500"
                >
                  <option value="">Select time</option>
                  {timeSlots.map(time => (
                    <option key={time} value={time}>{time}</option>
                  ))}
                </select>
                {errors.end_time && <p className="mt-1 text-sm text-red-600">{errors.end_time}</p>}
              </div>
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_available"
                checked={formData.is_available}
                onChange={(e) => setFormData({...formData, is_available: e.target.checked})}
                className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
              />
              <label htmlFor="is_available" className="ml-2 block text-sm text-gray-700">
                Available for appointments
              </label>
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50"
                disabled={submitting}
              >
                {submitting ? 'Adding...' : 'Add Availability'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const handleDeleteAvailability = async (slotId) => {
    if (!confirm('Are you sure you want to delete this availability slot?')) return;
    
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/doctor-availability/', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrf-token]')?.content || '',
        },
        body: JSON.stringify({ id: slotId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showToast('Availability deleted successfully!', 'success');
        // Remove from state
        setAvailability(prev => prev.filter(slot => slot.id !== slotId));
      } else {
        showToast(data.error || 'Failed to delete availability', 'error');
      }
    } catch (error) {
      console.error('Error deleting availability:', error);
      showToast('Failed to delete availability', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleAvailability = async (slotId, currentStatus) => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/toggle-availability/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.querySelector('[name=csrf-token]')?.content || '',
        },
        body: JSON.stringify({ id: slotId })
      });
      
      const data = await response.json();
      
      if (data.success) {
        showToast(data.message, 'success');
        // Update state
        setAvailability(prev => prev.map(slot => 
          slot.id === slotId 
            ? { ...slot, is_available: data.is_available }
            : slot
        ));
      } else {
        showToast(data.error || 'Failed to toggle availability', 'error');
      }
    } catch (error) {
      console.error('Error toggling availability:', error);
      showToast('Failed to toggle availability', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const groupAvailabilityByDay = () => {
    const grouped = {};
    daysOfWeek.forEach(day => {
      grouped[day.id] = availability.filter(slot => slot.day_of_week === day.id);
    });
    return grouped;
  };

  const groupedAvailability = groupAvailabilityByDay();

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-6 h-6 text-teal-600" />
            <h2 className="text-xl font-semibold text-gray-900">Schedule Management</h2>
          </div>
          
          <button
            onClick={() => setShowAddForm(true)}
            className="bg-teal-500 text-white px-4 py-2 rounded-lg hover:bg-teal-600 flex items-center gap-2"
            disabled={isLoading}
          >
            <Plus className="w-4 h-4" />
            Add Availability
          </button>
        </div>
      </div>
      
      <div className="p-6">
        <div className="space-y-6">
          {daysOfWeek.map(day => (
            <div key={day.id} className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-lg font-medium text-gray-900 mb-3 flex items-center gap-2">
                <Clock className="w-5 h-5 text-gray-500" />
                {day.name}
              </h3>
              
              {groupedAvailability[day.id]?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {groupedAvailability[day.id].map(slot => (
                    <div key={slot.id} className={`p-3 rounded-lg border ${
                      slot.is_available ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-900">
                          {slot.start_time} - {slot.end_time}
                        </span>
                        
                        <div className="flex gap-1">
                          <button
                            onClick={() => handleToggleAvailability(slot.id, slot.is_available)}
                            className={`px-2 py-1 text-xs rounded ${
                              slot.is_available 
                                ? 'bg-green-100 text-green-800 hover:bg-green-200' 
                                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                            }`}
                            disabled={isLoading}
                          >
                            {slot.is_available ? 'Available' : 'Disabled'}
                          </button>
                          
                          <button
                            onClick={() => handleDeleteAvailability(slot.id)}
                            className="p-1 text-red-600 hover:bg-red-50 rounded"
                            disabled={isLoading}
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                  <p>No availability set for {day.name}</p>
                  <button
                    onClick={() => setShowAddForm(true)}
                    className="mt-2 text-teal-600 hover:text-teal-700 text-sm font-medium"
                  >
                    Add availability
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {showAddForm && (
        <AddAvailabilityForm
          onClose={() => setShowAddForm(false)}
          onSave={() => {}} // Form handles its own save
        />
      )}
    </div>
  );
};

export default ScheduleManagement;