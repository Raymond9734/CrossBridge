import React from 'react';
import DashboardStats from '../DashBoardStats';
import { Search, Filter } from 'lucide-react';

// Doctor Dashboard Component
const DoctorDashboard = ({ showToast, dashboardData }) => {
    // Use real data from props or provide defaults
    const { stats = {}, appointments = [], patients = [] } = dashboardData || {};
    
    return (
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
                      </div>
                      <div className="flex gap-2">
                        <button 
                          className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full hover:bg-green-200"
                          onClick={() => showToast('Appointment completed', 'success')}
                        >
                          Complete
                        </button>
                        <button 
                          className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200"
                          onClick={() => showToast('Reschedule functionality coming soon', 'info')}
                        >
                          Reschedule
                        </button>
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
                        <p className="text-sm text-gray-600">Age: {patient.age}</p>
                        <p className="text-sm text-gray-500">Last visit: {patient.last_visit}</p>
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
    );
};
  
export default DoctorDashboard;