import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import AppointmentBookingModal from '../AppointmentModal';
import DashboardStats from '../DashBoardStats';
import mockData from '../../MockData/Data';



// Patient Dashboard Component
const PatientDashboard = ({ showToast }) => {
    const [showBookingModal, setShowBookingModal] = useState(false);
    
    return (
      <div className="space-y-6">
        <DashboardStats userRole="patient" />
        
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
              {mockData.appointments.slice(0, 3).map(appointment => (
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
              ))}
            </div>
          </div>
          
          {/* Recent Medical Records */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Medical Records</h3>
            <div className="space-y-3">
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="font-medium text-gray-900">Blood Test Results</p>
                <p className="text-sm text-gray-600">Dr. Sarah Johnson</p>
                <p className="text-sm text-gray-500">January 15, 2024</p>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="font-medium text-gray-900">X-Ray Report</p>
                <p className="text-sm text-gray-600">Dr. Michael Chen</p>
                <p className="text-sm text-gray-500">January 10, 2024</p>
              </div>
              <div className="p-4 border border-gray-200 rounded-lg">
                <p className="font-medium text-gray-900">Physical Examination</p>
                <p className="text-sm text-gray-600">Dr. Sarah Johnson</p>
                <p className="text-sm text-gray-500">January 8, 2024</p>
              </div>
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