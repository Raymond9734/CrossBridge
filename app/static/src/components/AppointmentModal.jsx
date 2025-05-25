import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { router } from '@inertiajs/react';

// Appointment Booking Modal
const AppointmentBookingModal = ({ isOpen, onClose, onBook, showToast }) => {
    const [selectedDoctor, setSelectedDoctor] = useState('');
    const [selectedDate, setSelectedDate] = useState('');
    const [selectedTime, setSelectedTime] = useState('');
    const [appointmentType, setAppointmentType] = useState('');
    const [notes, setNotes] = useState('');
    const [doctors, setDoctors] = useState([]);
    const [timeSlots, setTimeSlots] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    
    // Fetch doctors from backend API
    useEffect(() => {
        if (isOpen) {
            fetchDoctors();
        }
    }, [isOpen]);

    // Fetch available slots when doctor and date change
    useEffect(() => {
        if (selectedDoctor && selectedDate) {
            fetchAvailableSlots();
        }
    }, [selectedDoctor, selectedDate]);

    const fetchDoctors = async () => {
        try {
            const response = await fetch('/api/available-doctors/');
            const data = await response.json();
            setDoctors(data.doctors || []);
        } catch (error) {
            console.error('Failed to fetch doctors:', error);
            showToast('Failed to load doctors', 'error');
        }
    };

    const fetchAvailableSlots = async () => {
        try {
            const doctor = doctors.find(d => d.name === selectedDoctor);
            if (!doctor) return;

            const response = await fetch(`/api/available-slots/?doctor_id=${doctor.id}&date=${selectedDate}`);
            const data = await response.json();
            setTimeSlots(data.slots || []);
            setSelectedTime(''); // Reset selected time when slots change
        } catch (error) {
            console.error('Failed to fetch time slots:', error);
            showToast('Failed to load available times', 'error');
            setTimeSlots([]);
        }
    };
    
    const handleSubmit = async () => {
      if (!selectedDoctor || !selectedDate || !selectedTime || !appointmentType) {
          showToast('Please fill in all required fields', 'error');
          return;
      }
      
      setIsLoading(true);
      
      try {
          // Get CSRF token
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
  
          // Use fetch instead of router.post for API endpoint
          const response = await fetch('/api/book-appointment/', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCSRFToken(),
                  'X-CSRF-Token': getCSRFToken(),
              },
              body: JSON.stringify({
                  doctor: selectedDoctor,
                  date: selectedDate,
                  time: selectedTime,
                  type: appointmentType,
                  notes: notes
              })
          });
  
          const data = await response.json();
  
          if (response.ok && data.success) {
              showToast('Appointment booked successfully!', 'success');
              onClose();
              // Reset form
              setSelectedDoctor('');
              setSelectedDate('');
              setSelectedTime('');
              setAppointmentType('');
              setNotes('');
              // Refresh the page to show updated data
              window.location.reload();
          } else {
              showToast(data.error || 'Failed to book appointment', 'error');
          }
      } catch (error) {
          console.error('Booking error:', error);
          showToast('Failed to book appointment', 'error');
      } finally {
          setIsLoading(false);
      }
  };
    
    if (!isOpen) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-8 md:pt-16 p-4 z-50 !mt-0">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[85vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Book Appointment</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Doctor *</label>
              <select
                value={selectedDoctor}
                onChange={(e) => setSelectedDoctor(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                disabled={doctors.length === 0}
              >
                <option value="">
                  {doctors.length === 0 ? 'No available doctor' : 'Choose a doctor'}
                </option>
                {doctors.map(doctor => (
                  <option key={doctor.id} value={doctor.name} disabled={!doctor.available}>
                    {doctor.name} - {doctor.specialty} {!doctor.available && '(Unavailable)'}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Appointment Type *</label>
              <select
                value={appointmentType}
                onChange={(e) => setAppointmentType(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              >
                <option value="">Select type</option>
                <option value="Consultation">General Consultation</option>
                <option value="Follow-up">Follow-up Visit</option>
                <option value="Checkup">Regular Checkup</option>
                <option value="Emergency">Emergency</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Preferred Date *</label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Available Time Slots *</label>
              {selectedDoctor && selectedDate ? (
                <div className="grid grid-cols-2 gap-2">
                  {timeSlots.length > 0 ? (
                    timeSlots.map(time => (
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
                    ))
                  ) : (
                    <div className="col-span-2 text-center py-4 text-gray-500">
                      No available slots for this date
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-4 text-gray-500">
                  Please select a doctor and date to see available times
                </div>
              )}
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                placeholder="Any specific concerns or symptoms..."
              />
            </div>
            
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                disabled={isLoading}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50"
                disabled={isLoading}
              >
                {isLoading ? 'Booking...' : 'Book Appointment'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };
  
export default AppointmentBookingModal;