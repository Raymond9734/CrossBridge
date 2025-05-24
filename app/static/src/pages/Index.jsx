import React, { useState, useEffect } from 'react';
import { Calendar, Clock, User, Users, Bell, Settings, Menu, X, Plus, Search, Filter, CheckCircle, AlertCircle, Info } from 'lucide-react';

// Mock data for demonstration
const mockData = {
  user: { id: 1, name: 'Dr. Sarah Johnson', role: 'doctor', email: 'sarah@carebridge.com' },
  patients: [
    { id: 1, name: 'John Smith', age: 35, condition: 'Regular Checkup', lastVisit: '2024-01-15' },
    { id: 2, name: 'Mary Johnson', age: 42, condition: 'Diabetes Follow-up', lastVisit: '2024-01-10' },
    { id: 3, name: 'Robert Brown', age: 28, condition: 'Physical Therapy', lastVisit: '2024-01-12' }
  ],
  appointments: [
    { id: 1, patient: 'John Smith', doctor: 'Dr. Sarah Johnson', date: '2024-01-25', time: '10:00 AM', status: 'confirmed', type: 'Consultation' },
    { id: 2, patient: 'Mary Johnson', doctor: 'Dr. Sarah Johnson', date: '2024-01-25', time: '11:30 AM', status: 'pending', type: 'Follow-up' },
    { id: 3, patient: 'Robert Brown', doctor: 'Dr. Sarah Johnson', date: '2024-01-26', time: '2:00 PM', status: 'confirmed', type: 'Physical Therapy' }
  ],
  doctors: [
    { id: 1, name: 'Dr. Sarah Johnson', specialty: 'General Medicine', rating: 4.8, available: true },
    { id: 2, name: 'Dr. Michael Chen', specialty: 'Cardiology', rating: 4.9, available: true },
    { id: 3, name: 'Dr. Emily Rodriguez', specialty: 'Pediatrics', rating: 4.7, available: false }
  ]
};

// Toast Notification Component
const Toast = ({ message, type, isVisible, onClose }) => {
  useEffect(() => {
    if (isVisible) {
      const timer = setTimeout(onClose, 3000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  if (!isVisible) return null;

  const icons = {
    success: <CheckCircle className="w-5 h-5 text-green-500" />,
    error: <AlertCircle className="w-5 h-5 text-red-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />
  };

  const bgColors = {
    success: 'bg-green-50 border-green-200',
    error: 'bg-red-50 border-red-200',
    info: 'bg-blue-50 border-blue-200'
  };

  return (
    <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg border ${bgColors[type]} shadow-lg animate-pulse`}>
      <div className="flex items-center gap-3">
        {icons[type]}
        <span className="text-sm font-medium">{message}</span>
        <button onClick={onClose} className="ml-4 text-gray-400 hover:text-gray-600">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

// Sidebar Component
const Sidebar = ({ currentUser, activeView, setActiveView, isSidebarOpen, setIsSidebarOpen }) => {
  const patientNavItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Calendar },
    { id: 'appointments', label: 'My Appointments', icon: Clock },
    { id: 'book-appointment', label: 'Book Appointment', icon: Plus },
    { id: 'medical-records', label: 'Medical Records', icon: User },
    { id: 'profile', label: 'Profile', icon: Settings }
  ];

  const doctorNavItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Calendar },
    { id: 'schedule', label: 'My Schedule', icon: Clock },
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'appointments', label: 'Appointments', icon: Calendar },
    { id: 'profile', label: 'Profile', icon: Settings }
  ];

  const navItems = currentUser?.role === 'doctor' ? doctorNavItems : patientNavItems;

  return (
    <>
      {/* Mobile Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed top-0 left-0 h-full w-64 bg-white shadow-lg transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} transition-transform duration-300 ease-in-out z-50 lg:translate-x-0 lg:static lg:z-auto`}>
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-teal-600">CareBridge</h1>
          <p className="text-sm text-gray-600 mt-1">Healthcare Management</p>
        </div>
        
        <nav className="mt-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveView(item.id);
                  setIsSidebarOpen(false);
                }}
                className={`w-full flex items-center px-6 py-3 text-left hover:bg-teal-50 transition-colors ${
                  activeView === item.id ? 'bg-teal-50 text-teal-600 border-r-2 border-teal-600' : 'text-gray-700'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {item.label}
              </button>
            );
          })}
        </nav>
      </div>
    </>
  );
};

// Navbar Component
const Navbar = ({ currentUser, isSidebarOpen, setIsSidebarOpen }) => {
  const [showNotifications, setShowNotifications] = useState(false);
  
  return (
    <header className="bg-white shadow-sm border-b border-gray-200 px-4 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="lg:hidden p-2 rounded-md hover:bg-gray-100 mr-3"
          >
            <Menu className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-gray-900">Welcome back, {currentUser?.name}</h2>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-full hover:bg-gray-100 relative"
            >
              <Bell className="w-5 h-5 text-gray-600" />
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                3
              </span>
            </button>
            
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  <div className="p-4 hover:bg-gray-50 border-b border-gray-100">
                    <p className="font-medium text-sm">New appointment request</p>
                    <p className="text-xs text-gray-600 mt-1">John Smith requested an appointment for tomorrow</p>
                  </div>
                  <div className="p-4 hover:bg-gray-50 border-b border-gray-100">
                    <p className="font-medium text-sm">Appointment confirmed</p>
                    <p className="text-xs text-gray-600 mt-1">Your appointment with Dr. Johnson is confirmed</p>
                  </div>
                  <div className="p-4 hover:bg-gray-50">
                    <p className="font-medium text-sm">Medical records updated</p>
                    <p className="text-xs text-gray-600 mt-1">New test results are available</p>
                  </div>
                </div>
              </div>
            )}
          </div>
          
          <div className="flex items-center">
            <div className="w-8 h-8 bg-teal-500 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="ml-3 hidden sm:block">
              <p className="text-sm font-medium text-gray-900">{currentUser?.name}</p>
              <p className="text-xs text-gray-600 capitalize">{currentUser?.role}</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

// Dashboard Stats Component
const DashboardStats = ({ userRole }) => {
  const patientStats = [
    { label: 'Upcoming Appointments', value: '3', color: 'bg-blue-500' },
    { label: 'Completed Visits', value: '12', color: 'bg-green-500' },
    { label: 'Pending Reports', value: '2', color: 'bg-yellow-500' }
  ];

  const doctorStats = [
    { label: "Today's Appointments", value: '8', color: 'bg-blue-500' },
    { label: 'Total Patients', value: '142', color: 'bg-green-500' },
    { label: 'Pending Reviews', value: '5', color: 'bg-yellow-500' }
  ];

  const stats = userRole === 'doctor' ? doctorStats : patientStats;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {stats.map((stat, index) => (
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

// Appointment Booking Modal
const AppointmentBookingModal = ({ isOpen, onClose, onBook, showToast }) => {
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [appointmentType, setAppointmentType] = useState('');
  const [notes, setNotes] = useState('');
  
  const timeSlots = ['09:00 AM', '10:00 AM', '11:00 AM', '02:00 PM', '03:00 PM', '04:00 PM'];
  
  const handleSubmit = () => {
    if (!selectedDoctor || !selectedDate || !selectedTime || !appointmentType) {
      showToast('Please fill in all required fields', 'error');
      return;
    }
    
    onBook({
      doctor: selectedDoctor,
      date: selectedDate,
      time: selectedTime,
      type: appointmentType,
      notes
    });
    
    showToast('Appointment booked successfully!', 'success');
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
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
            >
              <option value="">Choose a doctor</option>
              {mockData.doctors.map(doctor => (
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
            <div className="grid grid-cols-2 gap-2">
              {timeSlots.map(time => (
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
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="flex-1 px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600"
            >
              Book Appointment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

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

// Doctor Dashboard Component
const DoctorDashboard = ({ showToast }) => {
  return (
    <div className="space-y-6">
      <DashboardStats userRole="doctor" />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's Schedule */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Today's Schedule</h3>
          <div className="space-y-3">
            {mockData.appointments.map(appointment => (
              <div key={appointment.id} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{appointment.patient}</p>
                    <p className="text-sm text-gray-600">{appointment.type}</p>
                    <p className="text-sm text-gray-500">{appointment.time}</p>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs bg-green-100 text-green-800 rounded-full hover:bg-green-200">
                      Complete
                    </button>
                    <button className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full hover:bg-blue-200">
                      Reschedule
                    </button>
                  </div>
                </div>
              </div>
            ))}
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
            {mockData.patients.map(patient => (
              <div key={patient.id} className="p-4 border border-gray-200 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{patient.name}</p>
                    <p className="text-sm text-gray-600">Age: {patient.age}</p>
                    <p className="text-sm text-gray-500">Last visit: {patient.lastVisit}</p>
                  </div>
                  <button className="px-3 py-1 text-xs bg-teal-100 text-teal-800 rounded-full hover:bg-teal-200">
                    View Profile
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Appointments List Component
const AppointmentsList = ({ userRole, showToast }) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredAppointments = mockData.appointments.filter(appointment => {
    const matchesFilter = filter === 'all' || appointment.status === filter;
    const matchesSearch = searchTerm === '' || 
      appointment.patient.toLowerCase().includes(searchTerm.toLowerCase()) ||
      appointment.doctor.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });
  
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
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              />
            </div>
            
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
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
            {filteredAppointments.map(appointment => (
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
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {appointment.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    <button className="text-teal-600 hover:text-teal-900">View</button>
                    <button className="text-blue-600 hover:text-blue-900">Edit</button>
                    <button className="text-red-600 hover:text-red-900">Cancel</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Profile Management Component
const ProfileManagement = ({ currentUser, showToast }) => {
  const [formData, setFormData] = useState({
    name: currentUser?.name || '',
    email: currentUser?.email || '',
    phone: '',
    address: '',
    emergencyContact: '',
    medicalHistory: ''
  });
  
  const handleSubmit = () => {
    showToast('Profile updated successfully!', 'success');
  };
  
  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };
  
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Profile Management</h2>
        <p className="text-sm text-gray-600 mt-1">Update your personal information</p>
      </div>
      
      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Emergency Contact</label>
            <input
              type="tel"
              name="emergencyContact"
              value={formData.emergencyContact}
              onChange={handleInputChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            />
          </div>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Address</label>
          <textarea
            name="address"
            value={formData.address}
            onChange={handleInputChange}
            rows={3}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          />
        </div>
        
        {currentUser?.role === 'patient' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Medical History</label>
            <textarea
              name="medicalHistory"
              value={formData.medicalHistory}
              onChange={handleInputChange}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              placeholder="Any allergies, chronic conditions, medications, etc."
            />
          </div>
        )}
        
        <div className="flex justify-end">
          <button
            type="button"
            onClick={handleSubmit}
            className="px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
          >
            Update Profile
          </button>
        </div>
      </div>
    </div>
  );
};

// Main Healthcare App Component
const HealthcareApp = () => {
  const [currentUser, setCurrentUser] = useState(mockData.user);
  const [activeView, setActiveView] = useState('dashboard');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [toast, setToast] = useState({ isVisible: false, message: '', type: 'info' });
  
  const showToast = (message, type = 'info') => {
    setToast({ isVisible: true, message, type });
  };
  
  const hideToast = () => {
    setToast({ ...toast, isVisible: false });
  };
  
  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return currentUser?.role === 'doctor' 
          ? <DoctorDashboard showToast={showToast} />
          : <PatientDashboard showToast={showToast} />;
      case 'appointments':
        return <AppointmentsList userRole={currentUser?.role} showToast={showToast} />;
      case 'book-appointment':
        return <PatientDashboard showToast={showToast} />;
      case 'profile':
        return <ProfileManagement currentUser={currentUser} showToast={showToast} />;
      case 'medical-records':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Medical Records</h2>
            <p className="text-gray-600">Medical records viewer would be implemented here with proper security and permission checks.</p>
          </div>
        );
      case 'schedule':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Schedule Management</h2>
            <p className="text-gray-600">Doctor schedule management interface would be implemented here.</p>
          </div>
        );
      case 'patients':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Patient Management</h2>
            <p className="text-gray-600">Patient list and management interface would be implemented here.</p>
          </div>
        );
      default:
        return <PatientDashboard showToast={showToast} />;
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast Notifications */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
      
      {/* Sidebar */}
      <Sidebar
        currentUser={currentUser}
        activeView={activeView}
        setActiveView={setActiveView}
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
      />
      
      {/* Main Content */}
      <div className="lg:ml-64">
        {/* Navbar */}
        <Navbar
          currentUser={currentUser}
          isSidebarOpen={isSidebarOpen}
          setIsSidebarOpen={setIsSidebarOpen}
        />
        
        {/* Page Content */}
        <main className="p-4 md:p-6">
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
};

export default HealthcareApp;