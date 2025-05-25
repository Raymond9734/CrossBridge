import React, { useState, useEffect } from 'react';
import { Search, Filter, Users, Calendar, Phone, MapPin, FileText, X, User, RefreshCw } from 'lucide-react';

const PatientManagement = ({ showToast }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showPatientModal, setShowPatientModal] = useState(false);
  const [patients, setPatients] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);

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

  // Fetch patients from API
  const fetchPatients = async () => {
    setIsFetching(true);
    try {
      const response = await apiCall('/api/v1/patient-management/patients/');
      
      if (response.success) {
        setPatients(response.patients || []);
      } else {
        console.error('Failed to fetch patients:', response.error);
        showToast('Failed to load patients data', 'error');
      }
    } catch (error) {
      console.error('Error fetching patients:', error);
      showToast('Failed to load patients data', 'error');
    } finally {
      setIsFetching(false);
    }
  };

  // Fetch detailed patient information
  const fetchPatientDetails = async (patientId) => {
    setIsLoading(true);
    try {
      const response = await apiCall(`/api/v1/patient-management/${patientId}/patient_detail/`);
      
      if (response.success) {
        return response.patient;
      } else {
        console.error('Failed to fetch patient details:', response.error);
        showToast('Failed to load patient details', 'error');
        return null;
      }
    } catch (error) {
      console.error('Error fetching patient details:', error);
      showToast('Failed to load patient details', 'error');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchPatients();
  }, []);

  // Filter patients when data or search changes
  useEffect(() => {
    const filtered = patients.filter(patient => 
      patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (patient.phone && patient.phone.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    setFilteredPatients(filtered);
  }, [patients, searchTerm]);

  const handleRefresh = () => {
    fetchPatients();
  };

  const handleViewPatientDetails = async (patient) => {
    const detailedPatient = await fetchPatientDetails(patient.id);
    if (detailedPatient) {
      setSelectedPatient(detailedPatient);
      setShowPatientModal(true);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Not provided';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const calculateAge = (birthDate) => {
    if (!birthDate) return 'Unknown';
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
    return age;
  };

  const PatientDetailModal = ({ patient, onClose }) => {
    if (!patient) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-teal-500 rounded-full flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{patient.name}</h2>
                  <p className="text-sm text-gray-600">Patient Details</p>
                </div>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Personal Information */}
              <div className="lg:col-span-2 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Personal Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Full Name</label>
                        <p className="mt-1 text-sm text-gray-900">{patient.name}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Age</label>
                        <p className="mt-1 text-sm text-gray-900">{calculateAge(patient.date_of_birth)} years</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                        <p className="mt-1 text-sm text-gray-900">{formatDate(patient.date_of_birth)}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Gender</label>
                        <p className="mt-1 text-sm text-gray-900">{patient.gender || 'Not specified'}</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Contact Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Email</label>
                        <p className="mt-1 text-sm text-gray-900">{patient.email}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Phone</label>
                        <p className="mt-1 text-sm text-gray-900">{patient.phone || 'Not provided'}</p>
                      </div>
                    </div>
                    {patient.address && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Address</label>
                        <p className="mt-1 text-sm text-gray-900">{patient.address}</p>
                      </div>
                    )}
                    {patient.emergency_contact && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Emergency Contact</label>
                          <p className="mt-1 text-sm text-gray-900">{patient.emergency_contact}</p>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Emergency Phone</label>
                          <p className="mt-1 text-sm text-gray-900">{patient.emergency_phone || 'Not provided'}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Medical History */}
                {patient.medical_history && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Medical History</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-900">{patient.medical_history}</p>
                    </div>
                  </div>
                )}
                
                {/* Insurance Information */}
                {patient.insurance_info && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Insurance Information</h3>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-900">{patient.insurance_info}</p>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Recent Activity */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                <div className="space-y-3">
                  {patient.recent_appointments?.length > 0 ? (
                    patient.recent_appointments.map(appointment => (
                      <div key={appointment.id} className="bg-gray-50 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar className="w-4 h-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-900">
                            {formatDate(appointment.date)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-600">{appointment.type}</p>
                        <span className={`inline-block px-2 py-1 text-xs rounded-full mt-1 ${
                          appointment.status === 'completed' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {appointment.status}
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-6 text-gray-500">
                      <Calendar className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p className="text-sm">No recent appointments</p>
                    </div>
                  )}
                </div>
                
                {/* Medical Records */}
                {patient.medical_records?.length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-medium text-gray-900 mb-3">Recent Medical Records</h4>
                    <div className="space-y-2">
                      {patient.medical_records.slice(0, 3).map(record => (
                        <div key={record.id} className="bg-gray-50 rounded-lg p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-900">
                              {formatDate(record.date)}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 truncate">
                            {record.diagnosis || 'General consultation'}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Quick Stats */}
                <div className="mt-6 space-y-3">
                  <h4 className="font-medium text-gray-900">Quick Stats</h4>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Appointments:</span>
                      <span className="font-medium text-gray-900">{patient.total_appointments || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Last Visit:</span>
                      <span className="font-medium text-gray-900">{patient.last_visit || 'Never'}</span>
                    </div>                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Patient Since:</span>
                      <span className="font-medium text-gray-900">{formatDate(patient.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <Users className="w-6 h-6 text-teal-600" />
            <h2 className="text-xl font-semibold text-gray-900">Patient Management</h2>
            {isFetching && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-teal-600"></div>
            )}
          </div>
          
          <div className="flex gap-3">
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
                placeholder="Search patients..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                disabled={isFetching}
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Loading state for initial fetch */}
      {isFetching && patients.length === 0 ? (
        <div className="p-6">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
            <span className="ml-3 text-gray-600">Loading patients...</span>
          </div>
        </div>
      ) : (
        <div className="p-6">
          {filteredPatients.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredPatients.map(patient => (
                <div key={patient.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-teal-600" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{patient.name}</h3>
                      <p className="text-sm text-gray-600">{calculateAge(patient.date_of_birth)} years old</p>
                    </div>
                  </div>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Phone className="w-4 h-4" />
                      <span>{patient.phone || 'No phone'}</span>
                    </div>
                    {patient.address && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <MapPin className="w-4 h-4" />
                        <span className="truncate">{patient.address}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>Last visit: {patient.last_visit || 'Never'}</span>
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewPatientDetails(patient)}
                      className="flex-1 px-3 py-2 bg-teal-500 text-white text-sm rounded-lg hover:bg-teal-600 transition-colors disabled:opacity-50"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Loading...' : 'View Details'}
                    </button>
                    <button
                      onClick={() => showToast('Medical records viewer coming soon', 'info')}
                      className="px-3 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <FileText className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Patients Found</h3>
              <p className="text-gray-600">
                {patients.length === 0 
                  ? "You don't have any patients yet. Patients will appear here after they book appointments with you."
                  : "No patients match your search criteria."
                }
              </p>
            </div>
          )}
        </div>
      )}
      
      {showPatientModal && selectedPatient && (
        <PatientDetailModal 
          patient={selectedPatient} 
          onClose={() => {
            setShowPatientModal(false);
            setSelectedPatient(null);
          }} 
        />
      )}
    </div>
  );
};

export default PatientManagement;