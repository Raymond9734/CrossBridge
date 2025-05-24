import React from 'react';

// Dashboard Stats Component
const DashboardStats = ({ userRole, stats = {} }) => {
 

  // Use real stats data
  const patientStats = [
    { 
      label: 'Upcoming Appointments', 
      value: String(stats.upcoming_appointments || 0), 
      color: 'bg-blue-500' 
    },
    { 
      label: 'Completed Visits', 
      value: String(stats.completed_visits || 0), 
      color: 'bg-green-500' 
    },
    { 
      label: 'Total Appointments', 
      value: String(stats.total_appointments || 0), 
      color: 'bg-yellow-500' 
    }
  ];

  const doctorStats = [
    { 
      label: "Today's Appointments", 
      value: String(stats.todays_appointments || 0), 
      color: 'bg-blue-500' 
    },
    { 
      label: 'Total Patients', 
      value: String(stats.total_patients || 0), 
      color: 'bg-green-500' 
    },
    { 
      label: 'Pending Reviews', 
      value: String(stats.pending_reviews || 0), 
      color: 'bg-yellow-500' 
    }
  ];

  const displayStats = userRole === 'doctor' ? doctorStats : patientStats;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {displayStats.map((stat, index) => (
        <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
              <span className="text-white font-bold text-lg">{stat.value}</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DashboardStats;