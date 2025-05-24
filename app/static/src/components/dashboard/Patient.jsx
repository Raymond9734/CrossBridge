import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import AppointmentBookingModal from '../AppointmentModal';
import DashboardStats from '../DashBoardStats';

// Patient Dashboard Component
const PatientDashboard = ({ showToast, dashboardData }) => {
    const [showBookingModal, setShowBookingModal] = useState(false);
    
    // Use real data from props or provide defaults
    const { stats = {}, appointments = [], medical_records = [] } = dashboardData || {};
    
    return (
      <div className="space-y-6">
        <DashboardStats 
          userRole="patient" 
          stats={stats}
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upcoming Appointments */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Upcoming Appointments</h3>
              <button
                onClick={() => setShowBookingModal(true)}
                className="bg-teal-500 text-white px-4 py-2 rounded-lg hover:bg-teal-600 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Book New
              </button>
            </div>
            
            <div className="space-y-3">
              {appointments.length > 0 ? (
                appointments.slice(0, 5).map(appointment => (
                  <div key={appointment.id} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900">{appointment.doctor}</p>
                        <p className="text-sm text-gray-600">{appointment.type}</p>
                        <p className="text-sm text-gray-500">{appointment.date} at {appointment.time}</p>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        appointment.status === 'confirmed' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {appointment.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500">No upcoming appointments</p>
                  <button
                    onClick={() => setShowBookingModal(true)}
                    className="mt-2 text-teal-600 hover:text-teal-700 font-medium"
                  >
                    Book your first appointment
                  </button>
                </div>
              )}
            </div>
          </div>
          
          {/* Recent Medical Records */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Medical Records</h3>
            <div className="space-y-3">
              {medical_records.length > 0 ? (
                medical_records.slice(0, 5).map(record => (
                  <div key={record.id} className="p-4 border border-gray-200 rounded-lg">
                    <p className="font-medium text-gray-900">{record.title}</p>
                    <p className="text-sm text-gray-600">{record.doctor}</p>
                    <p className="text-sm text-gray-500">{record.date}</p>
                  </div>
                ))
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500">No medical records yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <AppointmentBookingModal
          isOpen={showBookingModal}
          onClose={() => setShowBookingModal(false)}
          onBook={(appointmentData) => {
            console.log('Booking appointment:', appointmentData);
          }}
          showToast={showToast}
        />
      </div>
    );
  };
  
export default PatientDashboard;