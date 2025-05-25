import React, { useState, useEffect } from 'react';
import { Search, Filter, FileText, Calendar, User, Activity, X } from 'lucide-react';
import { usePage } from '@inertiajs/react';

const MedicalRecords = ({ showToast }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filteredRecords, setFilteredRecords] = useState([]);
  const [selectedRecord, setSelectedRecord] = useState(null);
  
  // Get medical records from backend - this would come from props
  const { medical_records = [], auth } = usePage().props;
  
  useEffect(() => {
    let filtered = medical_records.filter(record => {
      const matchesSearch = searchTerm === '' || 
        record.diagnosis.toLowerCase().includes(searchTerm.toLowerCase()) ||
        record.doctor_name.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesFilter = filterType === 'all' || 
        record.appointment_type === filterType;
      
      return matchesSearch && matchesFilter;
    });
    setFilteredRecords(filtered);
  }, [ searchTerm, filterType]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const RecordDetailModal = ({ record, onClose }) => {
    if (!record) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Medical Record Details</h2>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
          </div>
          
          <div className="p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                <p className="text-sm text-gray-900">{formatDate(record.date)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor</label>
                <p className="text-sm text-gray-900">{record.doctor_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Appointment Type</label>
                <p className="text-sm text-gray-900 capitalize">{record.appointment_type}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Duration</label>
                <p className="text-sm text-gray-900">{record.duration || '30'} minutes</p>
              </div>
            </div>
            
            {record.diagnosis && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Diagnosis</label>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-900">{record.diagnosis}</p>
                </div>
              </div>
            )}
            
            {record.treatment && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Treatment</label>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-900">{record.treatment}</p>
                </div>
              </div>
            )}
            
            {record.prescription && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Prescription</label>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-900">{record.prescription}</p>
                </div>
              </div>
            )}
            
            {/* Vitals */}
            {(record.blood_pressure || record.heart_rate || record.temperature || record.weight) && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Vital Signs</label>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {record.blood_pressure && (
                      <div>
                        <p className="text-xs text-gray-500">Blood Pressure</p>
                        <p className="text-sm font-medium text-gray-900">{record.blood_pressure}</p>
                      </div>
                    )}
                    {record.heart_rate && (
                      <div>
                        <p className="text-xs text-gray-500">Heart Rate</p>
                        <p className="text-sm font-medium text-gray-900">{record.heart_rate} bpm</p>
                      </div>
                    )}
                    {record.temperature && (
                      <div>
                        <p className="text-xs text-gray-500">Temperature</p>
                        <p className="text-sm font-medium text-gray-900">{record.temperature}°F</p>
                      </div>
                    )}
                    {record.weight && (
                      <div>
                        <p className="text-xs text-gray-500">Weight</p>
                        <p className="text-sm font-medium text-gray-900">{record.weight} lbs</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            {record.lab_results && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Lab Results</label>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-900">{record.lab_results}</p>
                </div>
              </div>
            )}
            
            {record.follow_up_required && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-yellow-600" />
                  <p className="text-sm font-medium text-yellow-800">Follow-up Required</p>
                </div>
                {record.follow_up_date && (
                  <p className="text-sm text-yellow-700 mt-1">
                    Scheduled for: {formatDate(record.follow_up_date)}
                  </p>
                )}
              </div>
            )}
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
            <FileText className="w-6 h-6 text-teal-600" />
            <h2 className="text-xl font-semibold text-gray-900">Medical Records</h2>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search records..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              />
            </div>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
            >
              <option value="all">All Types</option>
              <option value="consultation">Consultation</option>
              <option value="follow_up">Follow-up</option>
              <option value="checkup">Checkup</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
        </div>
      </div>
      
      <div className="p-6">
        {filteredRecords.length > 0 ? (
          <div className="space-y-4">
            {filteredRecords.map(record => (
              <div key={record.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Calendar className="w-4 h-4 text-gray-500" />
                      <span className="text-sm font-medium text-gray-900">{formatDate(record.date)}</span>
                      <span className="px-2 py-1 text-xs bg-teal-100 text-teal-800 rounded-full">
                        {record.appointment_type}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-700">{record.doctor_name}</span>
                    </div>
                    
                    {record.diagnosis && (
                      <p className="text-sm text-gray-600 mb-2">
                        <strong>Diagnosis:</strong> {record.diagnosis.substring(0, 100)}
                        {record.diagnosis.length > 100 && '...'}
                      </p>
                    )}
                    
                    {record.follow_up_required && (
                      <div className="flex items-center gap-2 text-sm text-yellow-600">
                        <Activity className="w-4 h-4" />
                        <span>Follow-up required</span>
                      </div>
                    )}
                  </div>
                  
                  <button
                    onClick={() => setSelectedRecord(record)}
                    className="px-4 py-2 text-sm bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors"
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Medical Records Found</h3>
            <p className="text-gray-600">
              {medical_records.length === 0 
                ? "You don't have any medical records yet. Visit a doctor to create your first record."
                : "No records match your search criteria. Try adjusting your filters."
              }
            </p>
          </div>
        )}
      </div>
      
      {selectedRecord && (
        <RecordDetailModal 
          record={selectedRecord} 
          onClose={() => setSelectedRecord(null)} 
        />
      )}
    </div>
  );
};

export default MedicalRecords;