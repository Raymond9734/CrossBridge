import React, { useState } from 'react';
import { X, Heart, FileText, AlertTriangle } from 'lucide-react';

const MedicalRecordForm = ({ appointment, isOpen, onClose, onSuccess, showToast }) => {
  const [formData, setFormData] = useState({
    diagnosis: '',
    treatment: '',
    prescription: '',
    lab_results: '',
    allergies: '',
    medications: '',
    medical_history: '',
    follow_up_required: false,
    follow_up_date: '',
    is_sensitive: false,
    // Vitals
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    heart_rate: '',
    temperature: '',
    weight: '',
    height: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.diagnosis.trim()) {
      newErrors.diagnosis = 'Diagnosis is required';
    }
    
    if (formData.follow_up_required && !formData.follow_up_date) {
      newErrors.follow_up_date = 'Follow-up date is required when follow-up is needed';
    }

    // Validate vitals if provided
    if (formData.blood_pressure_systolic && (formData.blood_pressure_systolic < 70 || formData.blood_pressure_systolic > 250)) {
      newErrors.blood_pressure_systolic = 'Systolic pressure must be between 70-250 mmHg';
    }
    
    if (formData.blood_pressure_diastolic && (formData.blood_pressure_diastolic < 40 || formData.blood_pressure_diastolic > 150)) {
      newErrors.blood_pressure_diastolic = 'Diastolic pressure must be between 40-150 mmHg';
    }

    if (formData.heart_rate && (formData.heart_rate < 30 || formData.heart_rate > 220)) {
      newErrors.heart_rate = 'Heart rate must be between 30-220 bpm';
    }

    if (formData.temperature && (formData.temperature < 95.0 || formData.temperature > 110.0)) {
      newErrors.temperature = 'Temperature must be between 95.0-110.0°F';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    
    try {
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

      const response = await fetch('/api/v1/medical-records/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken(),
          'X-CSRF-Token': getCSRFToken(),
        },
        body: JSON.stringify({
          appointment_id: appointment.id,
          ...formData
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        showToast('Medical record created successfully', 'success');
        onSuccess(data.medical_record);
        onClose();
      } else {
        setErrors(data.errors || { general: data.error || 'Failed to create medical record' });
      }
    } catch (error) {
      console.error('Error creating medical record:', error);
      setErrors({ general: 'Failed to create medical record' });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !appointment) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-6 h-6 text-teal-600" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Create Medical Record</h2>
                <p className="text-sm text-gray-600">
                  Patient: {appointment.patient} • Date: {appointment.date}
                </p>
              </div>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {errors.general && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              <span className="text-sm text-red-700">{errors.general}</span>
            </div>
          )}

          {/* Primary Assessment */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Primary Assessment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Diagnosis *
                </label>
                <textarea
                  name="diagnosis"
                  value={formData.diagnosis}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="Primary diagnosis and any secondary conditions..."
                />
                {errors.diagnosis && (
                  <p className="mt-1 text-sm text-red-600">{errors.diagnosis}</p>
                )}
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Treatment Plan
                </label>
                <textarea
                  name="treatment"
                  value={formData.treatment}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="Treatment plan, procedures performed, recommendations..."
                />
              </div>
            </div>
          </div>

          {/* Vitals */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Vital Signs</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Blood Pressure (Systolic)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="blood_pressure_systolic"
                    value={formData.blood_pressure_systolic}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="120"
                    min="70" max="250"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">mmHg</span>
                </div>
                {errors.blood_pressure_systolic && (
                  <p className="mt-1 text-sm text-red-600">{errors.blood_pressure_systolic}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Blood Pressure (Diastolic)
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="blood_pressure_diastolic"
                    value={formData.blood_pressure_diastolic}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="80"
                    min="40" max="150"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">mmHg</span>
                </div>
                {errors.blood_pressure_diastolic && (
                  <p className="mt-1 text-sm text-red-600">{errors.blood_pressure_diastolic}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Heart Rate
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="heart_rate"
                    value={formData.heart_rate}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="72"
                    min="30" max="220"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">bpm</span>
                </div>
                {errors.heart_rate && (
                  <p className="mt-1 text-sm text-red-600">{errors.heart_rate}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Temperature
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="temperature"
                    value={formData.temperature}
                    onChange={handleInputChange}
                    step="0.1"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="98.6"
                    min="95.0" max="110.0"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">°F</span>
                </div>
                {errors.temperature && (
                  <p className="mt-1 text-sm text-red-600">{errors.temperature}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Weight
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="weight"
                    value={formData.weight}
                    onChange={handleInputChange}
                    step="0.1"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="150"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">lbs</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Height
                </label>
                <div className="relative">
                  <input
                    type="number"
                    name="height"
                    value={formData.height}
                    onChange={handleInputChange}
                    step="0.1"
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                    placeholder="70"
                  />
                  <span className="absolute right-3 top-3 text-gray-500">inches</span>
                </div>
              </div>
            </div>
          </div>

          {/* Medications & Prescriptions */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Medications & Treatment</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Medications
                </label>
                <textarea
                  name="medications"
                  value={formData.medications}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="List current medications..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  New Prescriptions
                </label>
                <textarea
                  name="prescription"
                  value={formData.prescription}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="New prescriptions and dosage instructions..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Allergies
                </label>
                <textarea
                  name="allergies"
                  value={formData.allergies}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="Known allergies and reactions..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Lab Results
                </label>
                <textarea
                  name="lab_results"
                  value={formData.lab_results}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  placeholder="Lab test results and values..."
                />
              </div>
            </div>
          </div>

          {/* Follow-up */}
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-4">Follow-up Care</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="follow_up_required"
                  name="follow_up_required"
                  checked={formData.follow_up_required}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
                />
                <label htmlFor="follow_up_required" className="ml-2 text-sm text-gray-700">
                  Follow-up appointment required
                </label>
              </div>

              {formData.follow_up_required && (
                <div className="ml-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Date
                  </label>
                  <input
                    type="date"
                    name="follow_up_date"
                    value={formData.follow_up_date}
                    onChange={handleInputChange}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full md:w-auto p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
                  />
                  {errors.follow_up_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.follow_up_date}</p>
                  )}
                </div>
              )}

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_sensitive"
                  name="is_sensitive"
                  checked={formData.is_sensitive}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded"
                />
                <label htmlFor="is_sensitive" className="ml-2 text-sm text-gray-700 flex items-center gap-1">
                  <Heart className="w-4 h-4 text-red-500" />
                  Mark as sensitive/confidential record
                </label>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 disabled:opacity-50 font-medium"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating Record...' : 'Create Medical Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default MedicalRecordForm;