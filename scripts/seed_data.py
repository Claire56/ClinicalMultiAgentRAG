"""Seed script to populate database with fake healthcare data."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from faker import Faker
from datetime import datetime, timedelta
import random

from app.core.config import settings
from app.core.database import Base
from app.models.patient import Patient, Gender, BloodType
from app.models.medical_record import MedicalRecord, RecordType
from app.models.medication import Medication, MedicationStatus
from app.models.treatment import Treatment, TreatmentStatus
from app.models.user import User, UserRole
from app.core.security import get_password_hash

fake = Faker()
Faker.seed(42)  # For reproducible data


def create_users(session):
    """Create fake users."""
    print("Creating users...")
    
    users_data = [
        {
            "username": "admin",
            "email": "admin@healthcare.com",
            "hashed_password": get_password_hash("admin123"),
            "full_name": "Admin User",
            "role": UserRole.ADMIN,
            "is_active": True,
            "api_key": "test-api-key-admin-12345",
        },
        {
            "username": "dr.smith",
            "email": "dr.smith@healthcare.com",
            "hashed_password": get_password_hash("doctor123"),
            "full_name": "Dr. John Smith",
            "role": UserRole.PHYSICIAN,
            "is_active": True,
            "api_key": "test-api-key-physician-12345",
        },
        {
            "username": "nurse.jones",
            "email": "nurse.jones@healthcare.com",
            "hashed_password": get_password_hash("nurse123"),
            "full_name": "Nurse Mary Jones",
            "role": UserRole.NURSE,
            "is_active": True,
        },
    ]
    
    for user_data in users_data:
        user = User(**user_data)
        session.add(user)
    
    session.commit()
    print(f"Created {len(users_data)} users")


def create_patients(session, count=50):
    """Create fake patients."""
    print(f"Creating {count} patients...")
    
    patients = []
    for _ in range(count):
        patient = Patient(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=90),
            gender=random.choice(list(Gender)),
            blood_type=random.choice(list(BloodType)),
            email=fake.email(),
            phone=fake.phone_number(),
            address=fake.address(),
            emergency_contact_name=fake.name(),
            emergency_contact_phone=fake.phone_number(),
            medical_history_summary=fake.text(max_nb_chars=200),
            allergies=fake.text(max_nb_chars=100) if random.random() > 0.5 else None,
            current_medications=fake.text(max_nb_chars=150) if random.random() > 0.3 else None,
        )
        session.add(patient)
        patients.append(patient)
    
    session.commit()
    print(f"Created {len(patients)} patients")
    return patients


def create_medical_records(session, patients):
    """Create fake medical records."""
    print("Creating medical records...")
    
    record_types = list(RecordType)
    conditions = [
        "Hypertension", "Diabetes Type 2", "Asthma", "Arthritis",
        "Chest Pain", "Headache", "Back Pain", "Fever",
        "Cough", "Shortness of Breath", "Abdominal Pain",
    ]
    
    records = []
    for patient in patients:
        # Create 2-5 records per patient
        num_records = random.randint(2, 5)
        for _ in range(num_records):
            visit_date = fake.date_time_between(start_date="-2y", end_date="now")
            record = MedicalRecord(
                patient_id=patient.id,
                record_type=random.choice(record_types),
                title=f"{random.choice(conditions)} - {fake.word()}",
                description=fake.text(max_nb_chars=300),
                symptoms=fake.text(max_nb_chars=200),
                diagnosis=random.choice(conditions) if random.random() > 0.3 else None,
                notes=fake.text(max_nb_chars=250),
                physician_name=f"Dr. {fake.last_name()}",
                date_of_visit=visit_date,
            )
            session.add(record)
            records.append(record)
    
    session.commit()
    print(f"Created {len(records)} medical records")
    return records


def create_medications(session, patients):
    """Create fake medications."""
    print("Creating medications...")
    
    medication_names = [
        "Metformin", "Lisinopril", "Atorvastatin", "Amlodipine",
        "Metoprolol", "Omeprazole", "Losartan", "Albuterol",
        "Gabapentin", "Sertraline", "Levothyroxine", "Amlodipine",
    ]
    
    dosages = ["10mg", "20mg", "50mg", "100mg", "250mg", "500mg"]
    frequencies = ["Once daily", "Twice daily", "Three times daily", "As needed"]
    routes = ["Oral", "IV", "Topical", "Inhalation"]
    
    medications = []
    for patient in patients:
        # 30% of patients have active medications
        if random.random() > 0.7:
            num_meds = random.randint(1, 3)
            for _ in range(num_meds):
                start_date = fake.date_time_between(start_date="-1y", end_date="now")
                medication = Medication(
                    patient_id=patient.id,
                    medication_name=random.choice(medication_names),
                    dosage=random.choice(dosages),
                    frequency=random.choice(frequencies),
                    route=random.choice(routes),
                    start_date=start_date,
                    end_date=None if random.random() > 0.3 else start_date + timedelta(days=random.randint(30, 180)),
                    status=MedicationStatus.ACTIVE if random.random() > 0.2 else MedicationStatus.COMPLETED,
                    prescribing_physician=f"Dr. {fake.last_name()}",
                    notes=fake.text(max_nb_chars=100) if random.random() > 0.5 else None,
                )
                session.add(medication)
                medications.append(medication)
    
    session.commit()
    print(f"Created {len(medications)} medications")
    return medications


def create_treatments(session, patients):
    """Create fake treatments."""
    print("Creating treatments...")
    
    treatment_names = [
        "Physical Therapy", "Cardiac Rehabilitation", "Diabetes Management",
        "Hypertension Control", "Pain Management", "Respiratory Therapy",
        "Weight Management Program", "Mental Health Counseling",
    ]
    
    treatments = []
    for patient in patients:
        # 40% of patients have treatments
        if random.random() > 0.6:
            num_treatments = random.randint(1, 2)
            for _ in range(num_treatments):
                start_date = fake.date_time_between(start_date="-6m", end_date="now")
                treatment = Treatment(
                    patient_id=patient.id,
                    treatment_name=random.choice(treatment_names),
                    description=fake.text(max_nb_chars=200),
                    status=random.choice(list(TreatmentStatus)),
                    start_date=start_date,
                    end_date=start_date + timedelta(days=random.randint(30, 180)) if random.random() > 0.5 else None,
                    physician_name=f"Dr. {fake.last_name()}",
                    notes=fake.text(max_nb_chars=150) if random.random() > 0.5 else None,
                )
                session.add(treatment)
                treatments.append(treatment)
    
    session.commit()
    print(f"Created {len(treatments)} treatments")
    return treatments


def main():
    """Main seeding function."""
    print("Starting database seeding...")
    
    # Create sync engine for seeding
    engine = create_engine(settings.SYNC_DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    try:
        # Create users first
        create_users(session)
        
        # Create patients
        patients = create_patients(session, count=50)
        
        # Create related data
        create_medical_records(session, patients)
        create_medications(session, patients)
        create_treatments(session, patients)
        
        print("\n✅ Database seeding completed successfully!")
        print("\nTest credentials:")
        print("  Admin: username=admin, password=admin123")
        print("  Doctor: username=dr.smith, password=doctor123")
        print("  Nurse: username=nurse.jones, password=nurse123")
        print("\nAPI Keys:")
        print("  Admin: test-api-key-admin-12345")
        print("  Physician: test-api-key-physician-12345")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()

