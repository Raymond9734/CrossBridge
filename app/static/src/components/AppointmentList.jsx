import React, { useState, useEffect } from 'react';
import { User, Search } from 'lucide-react';
import { usePage, router } from '@inertiajs/react';

// Appointments List Component
const AppointmentsList = ({ userRole, showToast }) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredAppointments, setFilteredAppointments] = useState([]);
  
  // Get appointments from Inertia.js props
  const { appointments = [] } = usePage().props;
  
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
    // Update URL with filter parameter using Inertia.js
    router.get('/appointments/', { 
      status: newFilter === 'all' ? '' : newFilter,
      search: searchTerm || '' 
    }, { 
      preserveState: true,
      preserveScroll: true 
    });
  };

  const handleSearchChange = (newSearch) => {
    setSearchTerm(newSearch);
    // Debounce search to avoid too many requests
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      router.get('/appointments/', { 
        status: filter === 'all' ? '' : filter,
        search: newSearch 
      }, { 
        preserveState: true,
        preserveScroll: true 
      });
    }, 500);
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h2 className="text-xl font-semibold text-gray-900">Appointments</h2>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search appointments..."
                value={searchTerm}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              />
            </div>
            
            <select
              value={filter}
              onChange={(e) => handleFilterChange(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
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
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {appointment.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <div className="flex gap-2">
                      <button 
                        className="text-teal-600 hover:text-teal-900"
                        onClick={() => showToast('View appointment details coming soon', 'info')}
                      >
                        View
                      </button>
                      <button 
                        className="text-blue-600 hover:text-blue-900"
                        onClick={() => showToast('Edit appointment coming soon', 'info')}
                      >
                        Edit
                      </button>
                      <button 
                        className="text-red-600 hover:text-red-900"
                        onClick={() => showToast('Cancel appointment coming soon', 'info')}
                      >
                        Cancel
                      </button>
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
    </div>
  );
};

export default AppointmentsList;