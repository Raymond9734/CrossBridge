# app/management/__init__.py
# Empty file to make this a Python package

# app/management/commands/__init__.py
# Empty file to make this a Python package

# app/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta, time
from app.models import (
    UserProfile,
    DoctorProfile,
    DoctorAvailability,
    Appointment,
    MedicalRecord,
    Notification,
)


class Command(BaseCommand):
    help = "Create sample data for development and testing"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before creating new data",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            # Clear in reverse order to avoid foreign key constraints
            Notification.objects.all().delete()
            MedicalRecord.objects.all().delete()
            Appointment.objects.all().delete()
            DoctorAvailability.objects.all().delete()
            DoctorProfile.objects.all().delete()
            UserProfile.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared."))

        self.stdout.write("Creating sample data...")

        # Create doctors
        doctors_data = [
            {
                "username": "dr_sarah_johnson",
                "email": "sarah.johnson@carebridge.com",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "password": "password123",
                "specialty": "General Medicine",
                "license_number": "LIC-001234",
                "years_experience": 8,
                "rating": 4.8,
                "bio": "Experienced general practitioner with a focus on preventive care.",
                "phone": "+1234567890",
            },
            {
                "username": "dr_michael_chen",
                "email": "michael.chen@carebridge.com",
                "first_name": "Michael",
                "last_name": "Chen",
                "password": "password123",
                "specialty": "Cardiology",
                "license_number": "LIC-001235",
                "years_experience": 12,
                "rating": 4.9,
                "bio": "Cardiologist specializing in heart disease prevention and treatment.",
                "phone": "+1234567891",
            },
            {
                "username": "dr_emily_rodriguez",
                "email": "emily.rodriguez@carebridge.com",
                "first_name": "Emily",
                "last_name": "Rodriguez",
                "password": "password123",
                "specialty": "Pediatrics",
                "license_number": "LIC-001236",
                "years_experience": 6,
                "rating": 4.7,
                "bio": "Pediatrician with expertise in child development and family care.",
                "phone": "+1234567892",
            },
        ]

        doctors = []
        for doctor_data in doctors_data:
            # Create user
            user = User.objects.create_user(
                username=doctor_data["username"],
                email=doctor_data["email"],
                first_name=doctor_data["first_name"],
                last_name=doctor_data["last_name"],
                password=doctor_data["password"],
            )

            # Update user profile
            user_profile = user.userprofile
            user_profile.role = "doctor"
            user_profile.phone = doctor_data["phone"]
            user_profile.save()

            # Create doctor profile
            doctor_profile = DoctorProfile.objects.create(
                user_profile=user_profile,
                license_number=doctor_data["license_number"],
                specialty=doctor_data["specialty"],
                years_experience=doctor_data["years_experience"],
                rating=doctor_data["rating"],
                bio=doctor_data["bio"],
                is_available=True,
                accepts_new_patients=True,
                consultation_fee=150.00,
            )

            # Create availability schedule (Monday to Friday, 9 AM to 5 PM)
            for day in range(5):  # Monday to Friday
                DoctorAvailability.objects.create(
                    doctor=doctor_profile,
                    day_of_week=day,
                    start_time=time(9, 0),  # 9:00 AM
                    end_time=time(17, 0),  # 5:00 PM
                    is_available=True,
                )

            doctors.append(user)
            self.stdout.write(f"Created doctor: Dr. {user.get_full_name()}")

        # Create patients
        patients_data = [
            {
                "username": "john_smith",
                "email": "john.smith@example.com",
                "first_name": "John",
                "last_name": "Smith",
                "password": "password123",
                "phone": "+1234567893",
                "date_of_birth": "1989-05-15",
                "medical_history": "No known allergies. Regular checkups.",
                "address": "123 Main St, Springfield, IL 62701",
            },
            {
                "username": "mary_johnson",
                "email": "mary.johnson@example.com",
                "first_name": "Mary",
                "last_name": "Johnson",
                "password": "password123",
                "phone": "+1234567894",
                "date_of_birth": "1982-09-22",
                "medical_history": "Type 2 diabetes, managed with medication.",
                "address": "456 Oak Ave, Springfield, IL 62702",
            },
            {
                "username": "robert_brown",
                "email": "robert.brown@example.com",
                "first_name": "Robert",
                "last_name": "Brown",
                "password": "password123",
                "phone": "+1234567895",
                "date_of_birth": "1996-12-03",
                "medical_history": "Previous knee injury, ongoing physical therapy.",
                "address": "789 Pine St, Springfield, IL 62703",
            },
        ]

        patients = []
        for patient_data in patients_data:
            # Create user
            user = User.objects.create_user(
                username=patient_data["username"],
                email=patient_data["email"],
                first_name=patient_data["first_name"],
                last_name=patient_data["last_name"],
                password=patient_data["password"],
            )

            # Update user profile
            user_profile = user.userprofile
            user_profile.role = "patient"
            user_profile.phone = patient_data["phone"]
            user_profile.date_of_birth = datetime.strptime(
                patient_data["date_of_birth"], "%Y-%m-%d"
            ).date()
            user_profile.medical_history = patient_data["medical_history"]
            user_profile.address = patient_data["address"]
            user_profile.save()

            patients.append(user)
            self.stdout.write(f"Created patient: {user.get_full_name()}")

        # Create appointments
        appointments_data = [
            {
                "patient": patients[0],  # John Smith
                "doctor": doctors[0],  # Dr. Sarah Johnson
                "date": timezone.now().date() + timedelta(days=1),
                "time": time(10, 0),
                "type": "consultation",
                "status": "confirmed",
                "notes": "Annual physical examination",
            },
            {
                "patient": patients[1],  # Mary Johnson
                "doctor": doctors[0],  # Dr. Sarah Johnson
                "date": timezone.now().date() + timedelta(days=1),
                "time": time(11, 30),
                "type": "follow_up",
                "status": "pending",
                "notes": "Diabetes follow-up appointment",
            },
            {
                "patient": patients[2],  # Robert Brown
                "doctor": doctors[0],  # Dr. Sarah Johnson
                "date": timezone.now().date() + timedelta(days=2),
                "time": time(14, 0),
                "type": "physical_therapy",
                "status": "confirmed",
                "notes": "Physical therapy session for knee rehabilitation",
            },
            # Past appointments for medical records
            {
                "patient": patients[0],  # John Smith
                "doctor": doctors[0],  # Dr. Sarah Johnson
                "date": timezone.now().date() - timedelta(days=30),
                "time": time(10, 0),
                "type": "checkup",
                "status": "completed",
                "notes": "Regular health checkup",
            },
            {
                "patient": patients[1],  # Mary Johnson
                "doctor": doctors[1],  # Dr. Michael Chen
                "date": timezone.now().date() - timedelta(days=45),
                "time": time(15, 0),
                "type": "consultation",
                "status": "completed",
                "notes": "Cardiology consultation for diabetes-related concerns",
            },
        ]

        for apt_data in appointments_data:
            appointment = Appointment.objects.create(
                patient=apt_data["patient"],
                doctor=apt_data["doctor"],
                appointment_date=apt_data["date"],
                start_time=apt_data["time"],
                end_time=(
                    datetime.combine(apt_data["date"], apt_data["time"])
                    + timedelta(minutes=30)
                ).time(),
                appointment_type=apt_data["type"],
                status=apt_data["status"],
                patient_notes=apt_data["notes"],
                created_by=apt_data["patient"],
            )

            # Create medical records for completed appointments
            if apt_data["status"] == "completed":
                medical_record = MedicalRecord.objects.create(
                    appointment=appointment,
                    diagnosis=self.get_sample_diagnosis(apt_data["type"]),
                    treatment=self.get_sample_treatment(apt_data["type"]),
                    prescription=self.get_sample_prescription(apt_data["type"]),
                    follow_up_required=apt_data["type"]
                    in ["follow_up", "consultation"],
                )

                if medical_record.follow_up_required:
                    medical_record.follow_up_date = apt_data["date"] + timedelta(
                        days=30
                    )
                    medical_record.save()

            self.stdout.write(
                f'Created appointment: {apt_data["patient"].get_full_name()} with Dr. {apt_data["doctor"].get_full_name()}'
            )

        # Create notifications
        notifications_data = [
            {
                "user": patients[0],
                "type": "appointment_confirmed",
                "title": "Appointment Confirmed",
                "message": "Your appointment with Dr. Sarah Johnson has been confirmed for tomorrow at 10:00 AM.",
            },
            {
                "user": patients[1],
                "type": "appointment_reminder",
                "title": "Appointment Reminder",
                "message": "You have an upcoming appointment with Dr. Sarah Johnson tomorrow at 11:30 AM.",
            },
            {
                "user": doctors[0],
                "type": "appointment_confirmed",
                "title": "New Appointment Request",
                "message": "Robert Brown has requested an appointment for physical therapy.",
            },
        ]

        for notif_data in notifications_data:
            Notification.objects.create(
                user=notif_data["user"],
                notification_type=notif_data["type"],
                title=notif_data["title"],
                message=notif_data["message"],
                is_read=False,
            )
        self.create_additional_medical_records()

        self.stdout.write(f"Created {len(notifications_data)} notifications")

        # Create a superuser if one doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            admin_user = User.objects.create_superuser(
                username="admin",
                email="admin@carebridge.com",
                password="admin123",
                first_name="Admin",
                last_name="User",
            )
            admin_user.userprofile.role = "admin"
            admin_user.userprofile.save()
            self.stdout.write(
                "Created admin user (username: admin, password: admin123)"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created sample data:\n"
                f"- {len(doctors)} doctors\n"
                f"- {len(patients)} patients\n"
                f"- {len(appointments_data)} appointments\n"
                f"- {len(notifications_data)} notifications"
            )
        )

    def get_sample_diagnosis(self, appointment_type):
        diagnoses = {
            "consultation": "General health assessment completed. Patient in good overall health.",
            "follow_up": "Follow-up examination shows improvement in condition.",
            "checkup": "Routine checkup completed. All vital signs within normal range.",
            "physical_therapy": "Physical therapy session completed. Range of motion improving.",
        }
        return diagnoses.get(appointment_type, "Consultation completed.")

    def get_sample_treatment(self, appointment_type):
        treatments = {
            "consultation": "Recommended regular exercise and healthy diet.",
            "follow_up": "Continue current medication regimen.",
            "checkup": "No treatment required. Continue preventive care.",
            "physical_therapy": "Continue prescribed exercises and stretching routine.",
        }
        return treatments.get(appointment_type, "Treatment plan discussed.")

    def get_sample_prescription(self, appointment_type):
        prescriptions = {
            "consultation": "",
            "follow_up": "Continue current medications as prescribed.",
            "checkup": "",
            "physical_therapy": "Over-the-counter anti-inflammatory as needed.",
        }
        return prescriptions.get(appointment_type, "")

    def create_additional_medical_records(self):
        """Create additional medical records for better testing"""

        # Get existing completed appointments
        completed_appointments = Appointment.objects.filter(status="completed")

        for appointment in completed_appointments:
            # Create medical record if it doesn't exist
            if not hasattr(appointment, "medical_record"):
                medical_record = MedicalRecord.objects.create(
                    appointment=appointment,
                    diagnosis=self.get_sample_diagnosis(appointment.appointment_type),
                    treatment=self.get_sample_treatment(appointment.appointment_type),
                    prescription=self.get_sample_prescription(
                        appointment.appointment_type
                    ),
                    follow_up_required=appointment.appointment_type
                    in ["follow_up", "consultation"],
                    # Add some sample vitals
                    blood_pressure_systolic=120
                    + (appointment.id % 40),  # 120-160 range
                    blood_pressure_diastolic=80 + (appointment.id % 20),  # 80-100 range
                    heart_rate=60 + (appointment.id % 40),  # 60-100 range
                    temperature=98.6
                    + ((appointment.id % 10) - 5) * 0.2,  # 97.6-99.6 range
                    weight=150 + (appointment.id % 100),  # 150-250 range
                    height=60 + (appointment.id % 24),  # 5'0" to 7'0" range
                )

                if medical_record.follow_up_required:
                    medical_record.follow_up_date = (
                        appointment.appointment_date + timedelta(days=30)
                    )
                    medical_record.save()

    def get_enhanced_sample_diagnosis(self, appointment_type):
        """Enhanced diagnosis samples"""
        diagnoses = {
            "consultation": [
                "Patient presents with general fatigue and mild headaches. Physical examination reveals no acute abnormalities. Blood pressure within normal limits.",
                "Routine consultation for preventive care. Patient reports no significant health concerns. Recommended annual screenings up to date.",
                "Patient complains of occasional back pain. Examination shows mild muscle tension. No signs of serious pathology detected.",
            ],
            "follow_up": [
                "Follow-up visit shows significant improvement in previously reported symptoms. Patient compliance with medication regimen excellent.",
                "Continued monitoring of chronic condition. Lab results show improvement. Patient responding well to current treatment plan.",
                "Follow-up assessment demonstrates stable condition. No new symptoms reported. Continue current management approach.",
            ],
            "checkup": [
                "Annual physical examination completed. All vital signs within normal range. Patient in good general health.",
                "Comprehensive health screening performed. No significant abnormalities detected. Preventive care recommendations provided.",
                "Routine wellness visit. Patient maintains healthy lifestyle. All screening tests current and normal.",
            ],
            "physical_therapy": [
                "Physical therapy session focused on range of motion exercises. Patient shows gradual improvement in mobility.",
                "Continued rehabilitation program. Strength and flexibility measurements show positive progress.",
                "Therapeutic exercises performed. Patient demonstrates good compliance with home exercise program.",
            ],
        }

        diagnosis_list = diagnoses.get(
            appointment_type, ["General consultation completed."]
        )
        return diagnosis_list[hash(appointment_type) % len(diagnosis_list)]

    def get_enhanced_sample_treatment(self, appointment_type):
        """Enhanced treatment samples"""
        treatments = {
            "consultation": [
                "Recommended lifestyle modifications including regular exercise and stress management techniques. Advised adequate rest and hydration.",
                "Patient education provided on symptom management. Recommended follow-up if symptoms persist or worsen.",
                "Conservative management approach advised. Heat therapy and gentle stretching exercises recommended.",
            ],
            "follow_up": [
                "Continue current medication regimen with dosage adjustment as needed. Monitor symptoms closely.",
                "Treatment plan proving effective. No changes needed at this time. Continue current approach.",
                "Medication compliance excellent. Consider gradual dose reduction if improvement continues.",
            ],
            "checkup": [
                "No treatment required at this time. Continue current healthy lifestyle practices.",
                "Preventive care measures discussed. Immunizations updated as needed.",
                "Health maintenance counseling provided. Continue regular exercise and balanced diet.",
            ],
            "physical_therapy": [
                "Progressive exercise program advanced to next level. Home exercises modified accordingly.",
                "Continue current rehabilitation protocol. Additional strengthening exercises introduced.",
                "Therapeutic modalities applied. Patient education on injury prevention techniques provided.",
            ],
        }

        treatment_list = treatments.get(
            appointment_type, ["Treatment plan discussed with patient."]
        )
        return treatment_list[
            hash(appointment_type + "treatment") % len(treatment_list)
        ]

    def get_enhanced_sample_prescription(self, appointment_type):
        """Enhanced prescription samples"""
        prescriptions = {
            "consultation": [
                "Ibuprofen 400mg, take as needed for pain, maximum 3 times daily with food.",
                "Multivitamin supplement, one tablet daily with breakfast.",
                "",  # No prescription needed
            ],
            "follow_up": [
                "Continue current medications as prescribed. Metformin 500mg twice daily with meals.",
                "Lisinopril 10mg daily in the morning. Monitor blood pressure regularly.",
                "Omeprazole 20mg daily before breakfast for acid reflux symptoms.",
            ],
            "checkup": [
                "",  # Usually no prescription for routine checkups
                "Vitamin D3 1000 IU daily for overall health maintenance.",
                "",
            ],
            "physical_therapy": [
                "Topical anti-inflammatory gel, apply to affected area twice daily.",
                "Acetaminophen 500mg as needed for pain, maximum 4 times daily.",
                "",
            ],
        }

        prescription_list = prescriptions.get(appointment_type, [""])
        return prescription_list[
            hash(appointment_type + "prescription") % len(prescription_list)
        ]
