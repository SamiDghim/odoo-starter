#!/usr/bin/env python3
import random
import datetime
import odoo
from odoo import api, SUPERUSER_ID


def random_name():
    first = random.choice(['Alex', 'Sam', 'John', 'Marie', 'Ana', 'Liam', 'Noah', 'Emma', 'Olivia', 'Mia', 'Lucas', 'Sofia', 'Hugo', 'Lea', 'Zoe'])
    last = random.choice(['Dupont', 'Martin', 'Bernard', 'Petit', 'Robert', 'Richard', 'Durand', 'Moreau', 'Simon', 'Laurent'])
    return f"{first} {last}"


def main():
    # Target DB configured by docker-compose Odoo container
    odoo.tools.config.parse_config(['-d', 'medical_cabinet'])
    registry = odoo.registry('medical_cabinet')

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        Doctor = env['medical.doctor']
        Patient = env['medical.patient']
        Appointment = env['medical.appointment']
        Prescription = env['medical.prescription']

        # Parameters
        n_doctors = 15
        n_patients = 500

        print('Seeding medical_practice: creating', n_doctors, 'doctors and', n_patients, 'patients...')

        # Create doctors
        specialties = ['General Medicine', 'Pediatrics', 'Cardiology', 'Dermatology', 'Orthopedics', 'Neurology', 'ENT']
        doctors = []
        for i in range(n_doctors):
            name = f"Dr. {random_name()}"
            d = Doctor.create({
                'name': name,
                'speciality': random.choice(specialties),
                'email': f"{name.replace(' ', '.').lower()}@example.com",
            })
            doctors.append(d)

        # Create patients
        patients = []
        for i in range(n_patients):
            name = random_name()
            birth_date = (datetime.date.today() - datetime.timedelta(days=random.randint(18*365, 80*365))).isoformat()
            pvals = {
                'name': name,
                'birth_date': birth_date,
                'email': f"{name.replace(' ', '.').lower()}@example.com",
                'phone': f"06{random.randint(10000000,99999999)}",
            }
            p = Patient.create(pvals)
            # Randomly assign a primary doctor to some patients
            if random.random() < 0.35:
                p.doctor_id = random.choice(doctors)
            patients.append(p)

        # Create appointments: each patient 0..4 appointments
        appt_types = ['consultation', 'checkup', 'follow_up', 'emergency']
        created_appts = []
        for p in patients:
            for _ in range(random.randint(0, 4)):
                doc = random.choice(doctors)
                days_ago = random.randint(0, 180)
                hours = random.randint(8, 17)
                dt = datetime.datetime.now() - datetime.timedelta(days=days_ago, hours=random.randint(0, 72))
                appt = Appointment.create({
                    'patient_id': p.id,
                    'doctor_id': doc.id,
                    'appointment_date': dt,
                    'appointment_type': random.choice(appt_types),
                    'reason': random.choice(['Routine check', 'Follow-up', 'New symptom', 'Prescription refill'])
                })
                created_appts.append(appt)

        # Create prescriptions for a subset of appointments by creating prescription records
        # and adding prescription lines (model: medical.prescription.line) with realistic names and instructions
        medication_choices = [
            ('Amoxicillin', '500 mg', 'Three times daily', '7 days', 'Take after meals. Finish the full course.'),
            ('Ibuprofen', '200 mg', 'Every 6-8 hours as needed', '5 days', 'Do not exceed 1200 mg/day. Take with food if stomach upset.'),
            ('Paracetamol', '500 mg', 'Every 4-6 hours as needed', '3 days', 'Do not exceed 3000 mg/day.'),
            ('Hydrocortisone Cream 1%', 'Apply thin layer', 'Twice daily', '7 days', 'Apply to affected area only. Do not use on open wounds.'),
            ('Loratadine', '10 mg', 'Once daily', '10 days', 'Take at the same time each day.'),
        ]

        # Create drug master records and map names to ids
        Drug = env['medical.drug']
        drug_map = {}
        for med in ['Amoxicillin', 'Ibuprofen', 'Paracetamol', 'Hydrocortisone Cream 1%', 'Loratadine']:
            d = Drug.create({'name': med, 'code': med.split()[0].upper()})
            drug_map[med] = d

        n_presc = int(len(created_appts) * 0.25)
        for appt in random.sample(created_appts, n_presc if n_presc > 0 else 0):
            presc = Prescription.create({
                'patient_id': appt.patient_id.id,
                'doctor_id': appt.doctor_id.id,
                'appointment_id': appt.id,
                'notes': random.choice(['Take with food', 'Avoid driving after taking', 'Return for follow-up in 7 days', 'Use as needed for pain'])
            })
            # Add 1-3 medication lines
            for _ in range(random.randint(1, 3)):
                med = random.choice(medication_choices)
                presc_line_vals = {
                    'prescription_id': presc.id,
                    'medication_id': drug_map.get(med[0]).id if drug_map.get(med[0]) else False,
                    'medication_name': med[0],
                    'dosage': med[1],
                    'frequency': med[2],
                    'duration': med[3],
                    'quantity': float(random.randint(1, 30)),
                    'instructions': med[4],
                }
                env['medical.prescription.line'].create(presc_line_vals)

        # Commit (cursor context will commit on close)
        print('Created: doctors=', len(doctors), 'patients=', len(patients), 'appointments=', len(created_appts), 'prescriptions approx=', n_presc)


if __name__ == '__main__':
    main()
