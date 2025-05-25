import React, { useState, useEffect } from 'react';
import { User, Search, RefreshCw, FileText, Calendar, Clock, Edit3 } from 'lucide-react';
import MedicalRecordForm from './MedicalRecordForm';
import RescheduleModal from './RescheduleModal';

const AppointmentsList = ({ userRole, showToast }) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredAppointments, setFilteredAppointments] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

  // Modal states
  const [showMedicalRecordModal, setShowMedicalRecordModal] = useState(false);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);

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

  // Fetch appointments from API
  const fetchAppointments = async (statusFilter = filter, searchQuery = searchTerm) => {
    setIsFetching(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (searchQuery) {
        params.append('search', searchQuery);
      }
      
      const queryString = params.toString();
      const url = `/api/v1/appointments/${queryString ? `?${queryString}` : ''}`;
      
      const response = await apiCall(url);
      
      if (response.success) {
        setAppointments(response.appointments || []);
      } else {
        console.error('Failed to fetch appointments:', response.error);
        showToast('Failed to load appointments data', 'error');
      }
    } catch (error) {
      console.error('Error fetching appointments:', error);
      showToast('Failed to load appointments data', 'error');
    } finally {
      setIsFetching(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchAppointments();
  }, []);

  // Filter appointments when data, filter, or search changes
  useEffect(() => {
    let filtered = appointments.filter(appointment => {
      const matchesFilter = filter === 'all' || appointment.status === filter;
      const matchesSearch = searchTerm === '' || 
        appointment.patient.toLowerCase().includes(searchTerm.toLowerCase()) ||
        appointment.doctor.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });
    setFilteredAppointments(filtered);
  }, [appointments, filter, searchTerm]);

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    fetchAppointments(newFilter, searchTerm);
  };

  const handleSearchChange = (newSearch) => {
    setSearchTerm(newSearch);
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      fetchAppointments(filter, newSearch);
    }, 500);
  };

  const handleRefresh = () => {
    fetchAppointments(filter, searchTerm);
  };

  const handleCancelAppointment = async (appointmentId) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    
    setIsLoading(true);
    
    try {
      const response = await apiCall(`/api/v1/appointments/${appointmentId}/cancel/`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'Cancelled by user' })
      });
      
      if (response.success) {
        showToast('Appointment cancelled successfully', 'success');
        fetchAppointments(filter, searchTerm);
      } else {
        showToast(response.error || 'Failed to cancel appointment', 'error');
      }
    } catch (error) {
      console.error('Error cancelling appointment:', error);
      showToast('Failed to cancel appointment', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmAppointment = async (appointmentId) => {
    if (userRole !== 'doctor') return;
    
    setIsLoading(true);
    
    try {
      const response = await apiCall(`/api/v1/appointments/${appointmentId}/confirm/`, {
        method: 'POST'
      });
      
      if (response.success) {
        showToast('Appointment confirmed successfully', 'success');
        fetchAppointments(filter, searchTerm);
      } else {
        showToast(response.error || 'Failed to confirm appointment', 'error');
      }
    } catch (error) {
      console.error('Error confirming appointment:', error);
      showToast('Failed to confirm appointment', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Modal handlers
  const handleCreateMedicalRecord = (appointment) => {
    setSelectedAppointment(appointment);
    setShowMedicalRecordModal(true);
  };

  const handleRescheduleAppointment = (appointment) => {
    // Add doctor_id to appointment object for the modal
    const appointmentWithDoctorId = {
      ...appointment,
      doctor_id: appointment.doctor_id || appointment.id ,
      date: appointment.appointment_date || appointment.date,
      time: appointment.start_time || appointment.time,
      type: appointment.appointment_type || appointment.type
    };
    setSelectedAppointment(appointmentWithDoctorId);
    setShowRescheduleModal(true);
  };

  const handleMedicalRecordSuccess = (medicalRecord) => {
    showToast('Medical record created successfully', 'success');
    fetchAppointments(filter, searchTerm); // Refresh appointments
  };

  const handleRescheduleSuccess = (updatedAppointment) => {
    showToast('Appointment rescheduled successfully', 'success');
    fetchAppointments(filter, searchTerm); // Refresh appointments
  };

  const canCreateMedicalRecord = (appointment) => {
    return userRole === 'doctor' && 
           (appointment.status === 'confirmed' || appointment.status === 'completed') &&
           !appointment.has_medical_record;
  };

  const canReschedule = (appointment) => {
    return (appointment.status === 'pending' || appointment.status === 'confirmed') &&
           new Date(appointment.date) > new Date();
  };
  
  return (
    <>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-semibold text-gray-900">Appointments</h2>
              {isFetching && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-teal-600"></div>
              )}
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleRefresh}
                className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-2"
                disabled={isFetching}
              >
                <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="Search appointments..."
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  disabled={isFetching}
                />
              </div>
              
              <select
                value={filter}
                onChange={(e) => handleFilterChange(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                disabled={isFetching}
              >
                <option value="all">All Status</option>
                <option value="confirmed">Confirmed</option>
                <option value="pending">Pending</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* Loading state for initial fetch */}
        {isFetching && appointments.length === 0 ? (
          <div className="p-6">
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
              <span className="ml-3 text-gray-600">Loading appointments...</span>
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {userRole === 'doctor' ? 'Patient' : 'Doctor'}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredAppointments.length > 0 ? (
                  filteredAppointments.map(appointment => (
                    <tr key={appointment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-teal-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">
                              {userRole === 'doctor' ? appointment.patient : appointment.doctor}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{appointment.date}</div>
                        <div className="text-sm text-gray-500">{appointment.time}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-gray-900">{appointment.type}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          appointment.status === 'confirmed' 
                            ? 'bg-green-100 text-green-800'
                            : appointment.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : appointment.status === 'completed'
                            ? 'bg-blue-100 text-blue-800'
                            : appointment.status === 'cancelled'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex gap-2 flex-wrap">
                          <button 
                            className="text-teal-600 hover:text-teal-900"
                            onClick={() => showToast('Appointment details modal coming soon', 'info')}
                            disabled={isLoading || isFetching}
                          >
                            View
                          </button>
                          
                          {/* Doctor-specific actions */}
                          {userRole === 'doctor' && appointment.status === 'pending' && (
                            <button 
                              className="text-green-600 hover:text-green-900"
                              onClick={() => handleConfirmAppointment(appointment.id)}
                              disabled={isLoading || isFetching}
                            >
                              Confirm
                            </button>
                          )}

                          {/* Medical Record Creation - Doctors only */}
                          {canCreateMedicalRecord(appointment) && (
                            <button
                              className="text-blue-600 hover:text-blue-900 flex items-center gap-1"
                              onClick={() => handleCreateMedicalRecord(appointment)}
                              disabled={isLoading || isFetching}
                              title="Create Medical Record"
                            >
                              <FileText className="w-3 h-3" />
                              Record
                            </button>
                          )}

                          {/* Reschedule - Both roles */}
                          {canReschedule(appointment) && (
                            <button
                              className="text-purple-600 hover:text-purple-900 flex items-center gap-1"
                              onClick={() => handleRescheduleAppointment(appointment)}
                              disabled={isLoading || isFetching}
                              title="Reschedule Appointment"
                            >
                              <Edit3 className="w-3 h-3" />
                              Reschedule
                            </button>
                          )}
                          
                          {appointment.status !== 'completed' && appointment.status !== 'cancelled' && (
                            <button 
                              className="text-red-600 hover:text-red-900"
                              onClick={() => handleCancelAppointment(appointment.id)}
                              disabled={isLoading || isFetching}
                            >
                              Cancel
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-6 py-4 text-center text-gray-500">
                      {appointments.length === 0 ? 'No appointments found' : 'No appointments match your search criteria'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Medical Record Modal */}
      <MedicalRecordForm
        appointment={selectedAppointment}
        isOpen={showMedicalRecordModal}
        onClose={() => {
          setShowMedicalRecordModal(false);
          setSelectedAppointment(null);
        }}
        onSuccess={handleMedicalRecordSuccess}
        showToast={showToast}
      />

      {/* Reschedule Modal */}
      <RescheduleModal
        appointment={selectedAppointment}
        isOpen={showRescheduleModal}
        onClose={() => {
          setShowRescheduleModal(false);
          setSelectedAppointment(null);
        }}
        onSuccess={handleRescheduleSuccess}
        showToast={showToast}
      />
    </>
  );
};

export default AppointmentsList;