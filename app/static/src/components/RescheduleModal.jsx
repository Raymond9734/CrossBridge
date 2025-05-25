import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, AlertTriangle } from 'lucide-react';

const RescheduleModal = ({ appointment, isOpen, onClose, onSuccess, showToast }) => {
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [availableSlots, setAvailableSlots] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

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

  // Fetch available slots when date changes
  useEffect(() => {
    if (selectedDate && appointment) {
      fetchAvailableSlots();
    }
  }, [selectedDate, appointment]);

const fetchAvailableSlots = async () => {
    setIsLoading(true);
    try {
      // Use appointment.doctor_id directly (now available from API fix)
      const doctorId = appointment.doctor_id;
      
      if (!doctorId) {
        console.error('Doctor ID not available:', appointment);
        showToast('Unable to load doctor information', 'error');
        setAvailableSlots([]);
        return;
      }
  
      const response = await apiCall(
        `/api/v1/appointment-booking/available_slots/?doctor_id=${doctorId}&date=${selectedDate}`
      );
      
      if (response.success) {
        setAvailableSlots(response.slots || []);
      } else {
        console.error('Failed to fetch slots:', response.error);
        showToast('Failed to load available time slots', 'error');
        setAvailableSlots([]);
      }
      setSelectedTime(''); // Reset selected time when slots change
    } catch (error) {
      console.error('Failed to fetch available slots:', error);
      showToast('Failed to load available time slots', 'error');
      setAvailableSlots([]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // Also fix the reschedule API call to use proper time format
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedDate || !selectedTime) {
      setErrors({ general: 'Please select both date and time' });
      return;
    }
  
    setIsSubmitting(true);
    setErrors({});
    
    try {
      // Convert 12-hour format to 24-hour for API
      const convertTo24Hour = (time12h) => {
        const [time, modifier] = time12h.split(' ');
        let [hours, minutes] = time.split(':');
        if (hours === '12') {
          hours = '00';
        }
        if (modifier === 'PM') {
          hours = parseInt(hours, 10) + 12;
        }
        return `${String(hours).padStart(2, '0')}:${minutes}`;
      };
  
  
      const response = await apiCall(`/api/v1/appointments/${appointment.id}/reschedule/`, {
        method: 'POST',
        body: JSON.stringify({
          new_date: selectedDate,
          new_time: convertTo24Hour(selectedTime) // Convert to 24-hour format
        })
      });
  
      if (response.success) {
        showToast('Appointment rescheduled successfully', 'success');
        onSuccess(response.appointment);
        onClose();
      } else {
        setErrors({ general: response.error || 'Failed to reschedule appointment' });
      }
    } catch (error) {
      console.error('Error rescheduling appointment:', error);
      setErrors({ general: 'Failed to reschedule appointment' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setSelectedDate('');
    setSelectedTime('');
    setAvailableSlots([]);
    setErrors({});
    onClose();
  };

  if (!isOpen || !appointment) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Calendar className="w-6 h-6 text-teal-600" />
              <h2 className="text-xl font-semibold text-gray-900">Reschedule Appointment</h2>
            </div>
            <button onClick={handleClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.general && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700">{errors.general}</span>
            </div>
          )}

          {/* Current Appointment Info */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-2">Current Appointment</h3>
            <div className="text-sm text-gray-600 space-y-1">
              <p><strong>Patient:</strong> {appointment.patient}</p>
              <p><strong>Doctor:</strong> {appointment.doctor}</p>
              <p><strong>Current Date:</strong> {appointment.date}</p>
              <p><strong>Current Time:</strong> {appointment.time}</p>
              <p><strong>Type:</strong> {appointment.type}</p>
            </div>
          </div>

          {/* New Date Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              New Date *
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              required
            />
          </div>

          {/* Available Time Slots */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Available Time Slots *
            </label>
            {selectedDate ? (
              <div>
                {isLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600"></div>
                    <span className="ml-2 text-gray-600">Loading available times...</span>
                  </div>
                ) : availableSlots.length > 0 ? (
                  <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                    {availableSlots.map(time => (
                      <button
                        key={time}
                        type="button"
                        onClick={() => setSelectedTime(time)}
                        className={`p-2 text-sm rounded-lg border transition-colors ${
                          selectedTime === time
                            ? 'bg-teal-500 text-white border-teal-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {time}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500 bg-gray-50 rounded-lg">
                    <Clock className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>No available slots for this date</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500 bg-gray-50 rounded-lg">
                <Calendar className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p>Please select a date to see available times</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 font-medium"
              disabled={isSubmitting || !selectedDate || !selectedTime}
            >
              {isSubmitting ? 'Rescheduling...' : 'Reschedule'}
            </button>
          </div>

          {/* Warning */}
          <div className="text-xs text-gray-500 text-center">
            Both patient and doctor will be notified of the schedule change
          </div>
        </form>
      </div>
    </div>
  );
};

export default RescheduleModal;