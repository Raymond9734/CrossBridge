import React, { useState } from 'react';
import DashboardStats from '../DashBoardStats';
import RescheduleModal from '../RescheduleModal';
import { Search, Filter } from 'lucide-react';

// Doctor Dashboard Component
const DoctorDashboard = ({ showToast, dashboardData, refreshData }) => {
    // Use real data from props or provide defaults
    const { stats = {}, appointments = [], patients = [] } = dashboardData || {};
    
    // Modal states
    const [showRescheduleModal, setShowRescheduleModal] = useState(false);
    const [selectedAppointment, setSelectedAppointment] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

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

    // Complete appointment handler
    const handleCompleteAppointment = async (appointment) => {
        if (!confirm(`Mark appointment with ${appointment.patient} as completed?`)) return;
        
        setIsLoading(true);
        
        try {
            // Update appointment status to completed
            const response = await apiCall(`/api/v1/appointments/${appointment.id}/`, {
                method: 'PATCH',
                body: JSON.stringify({ status: 'completed' })
            });

            if (response.success) {
                showToast('Appointment marked as completed', 'success');
                // Refresh dashboard data
                if (refreshData) {
                    refreshData();
                }
            } else {
                showToast(response.error || 'Failed to complete appointment', 'error');
            }
        } catch (error) {
            console.error('Error completing appointment:', error);
            showToast('Failed to complete appointment', 'error');
        } finally {
            setIsLoading(false);
        }
    };

    // Reschedule appointment handler
    const handleRescheduleAppointment = (appointment) => {
        // Add doctor_id if not present
        const appointmentWithDoctorId = {
            ...appointment,
            doctor_id: appointment.doctor_id || appointment.id,
            // Ensure we have the required fields for the modal
            doctor: appointment.doctor || 'Current Doctor',
            date: appointment.date || new Date().toISOString().split('T')[0],
            time: appointment.time || '12:00 PM',
            type: appointment.type || 'Consultation'
        };
        
        setSelectedAppointment(appointmentWithDoctorId);
        setShowRescheduleModal(true);
    };

    // Reschedule success handler
    const handleRescheduleSuccess = (updatedAppointment) => {
        showToast('Appointment rescheduled successfully', 'success');
        setShowRescheduleModal(false);
        setSelectedAppointment(null);
        
        // Refresh dashboard data
        if (refreshData) {
            refreshData();
        }
    };

    // Check if appointment can be completed
    const canComplete = (appointment) => {
        return appointment.status === 'confirmed' || appointment.status === 'in_progress';
    };

    // Check if appointment can be rescheduled
    const canReschedule = (appointment) => {
        return (appointment.status === 'pending' || appointment.status === 'confirmed') &&
               new Date(appointment.date || new Date()) > new Date();
    };
    
    return (
        <>
            <div className="space-y-6">
                <DashboardStats 
                    userRole="doctor" 
                    stats={stats}
                />
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Today's Schedule */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Schedule</h3>
                        <div className="space-y-3">
                            {appointments.length > 0 ? (
                                appointments.map(appointment => (
                                    <div key={appointment.id} className="p-4 border border-gray-200 rounded-lg">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p className="font-medium text-gray-900">{appointment.patient}</p>
                                                <p className="text-sm text-gray-600">{appointment.type}</p>
                                                <p className="text-sm text-gray-500">{appointment.time}</p>
                                                {appointment.status && (
                                                    <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                                                        appointment.status === 'confirmed' 
                                                            ? 'bg-green-100 text-green-800'
                                                            : appointment.status === 'pending'
                                                            ? 'bg-yellow-100 text-yellow-800'
                                                            : appointment.status === 'completed'
                                                            ? 'bg-blue-100 text-blue-800'
                                                            : 'bg-gray-100 text-gray-800'
                                                    }`}>
                                                        {appointment.status}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex gap-2 flex-wrap">
                                                {canComplete(appointment) && (
                                                    <button 
                                                        className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full hover:bg-green-200 disabled:opacity-50"
                                                        onClick={() => handleCompleteAppointment(appointment)}
                                                        disabled={isLoading}
                                                    >
                                                        {isLoading ? 'Processing...' : 'Complete'}
                                                    </button>
                                                )}
                                                
                                                {canReschedule(appointment) && (
                                                    <button 
                                                        className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200 disabled:opacity-50"
                                                        onClick={() => handleRescheduleAppointment(appointment)}
                                                        disabled={isLoading}
                                                    >
                                                        Reschedule
                                                    </button>
                                                )}

                                                {appointment.status === 'completed' && (
                                                    <span className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-full">
                                                        Completed
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-4">
                                    <p className="text-gray-500">No appointments scheduled for today</p>
                                </div>
                            )}
                        </div>
                    </div>
                    
                    {/* Patient Overview */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-gray-900">Recent Patients</h3>
                            <div className="flex gap-2">
                                <Search className="w-4 h-4 text-gray-400" />
                                <Filter className="w-4 h-4 text-gray-400" />
                            </div>
                        </div>
                        <div className="space-y-3">
                            {patients.length > 0 ? (
                                patients.map(patient => (
                                    <div key={patient.id} className="p-4 border border-gray-200 rounded-lg">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p className="font-medium text-gray-900">{patient.name}</p>
                                                <p className="text-sm text-gray-600">Age: {patient.age || 'N/A'}</p>
                                                <p className="text-sm text-gray-500">Last visit: {patient.last_visit || 'Never'}</p>
                                            </div>
                                            <button 
                                                className="px-3 py-1 text-xs bg-teal-100 text-teal-800 rounded-full hover:bg-teal-200"
                                                onClick={() => showToast('Patient profile functionality coming soon', 'info')}
                                            >
                                                View Profile
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center py-4">
                                    <p className="text-gray-500">No recent patients</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

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
  
export default DoctorDashboard;