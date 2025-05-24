// Mock data for demonstration
const mockData = {
  user: { id: 1, name: 'Dr. Sarah Johnson', role: 'patient', email: 'sarah@carebridge.com' },
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

export default mockData;
