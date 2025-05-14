import sqlite3 as sq
import os

db_path = "vaccinedatabase.db"

# Remove the old database file to recreate it cleanly (optional)
if os.path.exists(db_path):
    os.remove(db_path)

conn = sq.connect(db_path)
cursor = conn.cursor()

# Create the main tables
cursor.executescript("""
CREATE TABLE Person (
    idperson INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    familyname TEXT NOT NULL,
    dateofbirth TEXT NOT NULL -- Storing as TEXT, consider YYYY-MM-DD format
);

CREATE TABLE Credentials (
    email TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('doctor', 'patient', 'nurse', 'center_admin')),
    person_id INTEGER UNIQUE, -- Ensure one credential per person
    FOREIGN KEY (person_id) REFERENCES Person(idperson)
);

CREATE TABLE Doctor (
    iddoctor INTEGER PRIMARY KEY AUTOINCREMENT,
    idperson INTEGER NOT NULL UNIQUE, -- Ensure one doctor profile per person
    FOREIGN KEY (idperson) REFERENCES Person(idperson)
);

CREATE TABLE Nurse (
    idnurse INTEGER PRIMARY KEY AUTOINCREMENT,
    idperson INTEGER NOT NULL UNIQUE, -- Ensure one nurse profile per person
    FOREIGN KEY (idperson) REFERENCES Person(idperson)
);

CREATE TABLE CenterAdmin (
    idadmin INTEGER PRIMARY KEY AUTOINCREMENT,
    idperson INTEGER NOT NULL UNIQUE, -- Ensure one admin profile per person
    FOREIGN KEY (idperson) REFERENCES Person(idperson)
);

CREATE TABLE Patient (
    idpatient INTEGER PRIMARY KEY AUTOINCREMENT,
    idperson INTEGER NOT NULL UNIQUE, -- Ensure one patient profile per person
    FOREIGN KEY (idperson) REFERENCES Person(idperson)
);

-- Junction table to link doctors and their patients
CREATE TABLE DoctorPatient (
    iddoctor INTEGER,
    idpatient INTEGER,
    PRIMARY KEY (iddoctor, idpatient), -- Ensures a doctor can only be linked to a patient once
    FOREIGN KEY (iddoctor) REFERENCES Doctor(iddoctor),
    FOREIGN KEY (idpatient) REFERENCES Patient(idpatient)
);

CREATE TABLE Medicine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Med_name TEXT NOT NULL UNIQUE -- Vaccine names should be unique
);

CREATE TABLE Prescription (
    id_prescription INTEGER PRIMARY KEY AUTOINCREMENT,
    idpatient INTEGER,
    id_medicine INTEGER, -- Renamed from id_vaccine to match Medicine table
    iddoctor INTEGER,
    quantity INTEGER DEFAULT 1, -- Added quantity for prescription
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'administered', 'cancelled')), -- Added more statuses
    prescription_date TEXT, -- Date of prescription
    FOREIGN KEY (idpatient) REFERENCES Patient(idpatient),
    FOREIGN KEY (id_medicine) REFERENCES Medicine(id),
    FOREIGN KEY (iddoctor) REFERENCES Doctor(iddoctor)
);

CREATE TABLE VaccinationCenter (
    idcenter INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    address TEXT,
    admin_id INTEGER UNIQUE, -- Assuming one admin per center
    FOREIGN KEY (admin_id) REFERENCES CenterAdmin(idadmin)
);

CREATE TABLE CenterStock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    center_id INTEGER,
    vaccine_id INTEGER, -- This refers to Medicine.id
    quantity INTEGER DEFAULT 0,
    last_updated TEXT, -- Timestamp for when the stock was last updated
    UNIQUE (center_id, vaccine_id), -- Ensures one stock entry per vaccine per center
    FOREIGN KEY (center_id) REFERENCES VaccinationCenter(idcenter),
    FOREIGN KEY (vaccine_id) REFERENCES Medicine(id)
);

CREATE TABLE AdministrationLog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER UNIQUE, -- A prescription should only be administered once
    nurse_id INTEGER,
    center_id INTEGER, -- Center where the vaccine was administered
    administered_at TEXT, -- Timestamp of administration
    FOREIGN KEY (prescription_id) REFERENCES Prescription(id_prescription),
    FOREIGN KEY (nurse_id) REFERENCES Nurse(idnurse),
    FOREIGN KEY (center_id) REFERENCES VaccinationCenter(idcenter)
);
""")

# Insert sample data
# -----------------------------------
# Persons
persons_data = [
    ('John', 'Doe', '1980-01-15'),      # Person ID 1 (Doctor)
    ('Alice', 'Smith', '1990-04-10'),   # Person ID 2 (Doctor)
    ('Robert', 'Patient', '2000-06-01'),# Person ID 3 (Patient)
    ('Laura', 'Palmer', '2001-07-21'),  # Person ID 4 (Patient)
    ('Michael', 'Nurse', '1985-03-30'), # Person ID 5 (Nurse)
    ('Claire', 'Admin', '1970-12-12'),  # Person ID 6 (Center Admin)
    ('David', 'Lee', '1992-08-25')      # Person ID 7 (Nurse)
]
cursor.executemany("INSERT INTO Person (firstname, familyname, dateofbirth) VALUES (?, ?, ?)", persons_data)

# Roles and Credentials
# Doctor 1
cursor.execute("INSERT INTO Doctor (idperson) VALUES (1)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('doc1@example.com', 'password123', 'doctor', 1)")

# Doctor 2
cursor.execute("INSERT INTO Doctor (idperson) VALUES (2)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('doc2@example.com', 'password123', 'doctor', 2)")

# Patient 1
cursor.execute("INSERT INTO Patient (idperson) VALUES (3)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('patient1@example.com', 'password123', 'patient', 3)")

# Patient 2
cursor.execute("INSERT INTO Patient (idperson) VALUES (4)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('patient2@example.com', 'password123', 'patient', 4)")

# Nurse 1
cursor.execute("INSERT INTO Nurse (idperson) VALUES (5)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('nurse1@example.com', 'password123', 'nurse', 5)")

# Center Admin 1
cursor.execute("INSERT INTO CenterAdmin (idperson) VALUES (6)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('admin1@example.com', 'password123', 'center_admin', 6)")

# Nurse 2
cursor.execute("INSERT INTO Nurse (idperson) VALUES (7)")
cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES ('nurse2@example.com', 'password123', 'nurse', 7)")


# Link patients to doctors (DoctorPatient table uses Doctor.iddoctor and Patient.idpatient)
# Assuming Doctor with idperson=1 has iddoctor=1, Patient with idperson=3 has idpatient=1, etc.
cursor.execute("INSERT INTO DoctorPatient (iddoctor, idpatient) VALUES (1, 1)") # John Doe (doc) - Robert Patient (pat)
cursor.execute("INSERT INTO DoctorPatient (iddoctor, idpatient) VALUES (1, 2)") # John Doe (doc) - Laura Palmer (pat)
cursor.execute("INSERT INTO DoctorPatient (iddoctor, idpatient) VALUES (2, 2)") # Alice Smith (doc) - Laura Palmer (pat)


# Available Vaccines (Medicines)
vaccines_data = [
    ('COVID-19 Vaccine (Pfizer)',),
    ('Influenza Vaccine (Flu Shot)',),
    ('Hepatitis B Vaccine',),
    ('MMR Vaccine (Measles, Mumps, Rubella)',)
]
cursor.executemany("INSERT INTO Medicine (Med_name) VALUES (?)", vaccines_data)

# Vaccination Centers
# Center Admin with idperson=6 has idadmin=1
cursor.execute("INSERT INTO VaccinationCenter (name, address, admin_id) VALUES ('City Central Vaccination Clinic', '123 Health St, Anytown', 1)")
cursor.execute("INSERT INTO VaccinationCenter (name, address) VALUES ('Community Health Hub', '456 Wellness Ave, Otherville')") # No admin assigned initially

# Stock for Centers (CenterStock uses VaccinationCenter.idcenter and Medicine.id)
# City Central Vaccination Clinic (idcenter=1)
cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (1, 1, 100, datetime('now'))") # Pfizer
cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (1, 2, 150, datetime('now'))") # Flu Shot
cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (1, 3, 75, datetime('now'))")  # Hep B

# Community Health Hub (idcenter=2)
cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (2, 1, 50, datetime('now'))")  # Pfizer
cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (2, 4, 60, datetime('now'))")  # MMR


# Sample Prescriptions (Prescription uses Patient.idpatient, Medicine.id, Doctor.iddoctor)
# Patient 1 (Robert, idpatient=1), Vaccine: Pfizer (id=1), Doctor: John Doe (iddoctor=1)
cursor.execute("INSERT INTO Prescription (idpatient, id_medicine, iddoctor, quantity, status, prescription_date) VALUES (1, 1, 1, 1, 'pending', date('now'))")
# Patient 2 (Laura, idpatient=2), Vaccine: Flu Shot (id=2), Doctor: John Doe (iddoctor=1)
cursor.execute("INSERT INTO Prescription (idpatient, id_medicine, iddoctor, quantity, status, prescription_date) VALUES (2, 2, 1, 1, 'pending', date('now'))")
# Patient 2 (Laura, idpatient=2), Vaccine: Hep B (id=3), Doctor: Alice Smith (iddoctor=2)
cursor.execute("INSERT INTO Prescription (idpatient, id_medicine, iddoctor, quantity, status, prescription_date) VALUES (2, 3, 2, 1, 'administered', date('now', '-7 days'))")


# Sample Administration Log (AdministrationLog uses Prescription.id_prescription, Nurse.idnurse, VaccinationCenter.idcenter)
# For the administered prescription (id_prescription=3), Nurse: Michael Nurse (idnurse=1), Center: City Central (idcenter=1)
cursor.execute("INSERT INTO AdministrationLog (prescription_id, nurse_id, center_id, administered_at) VALUES (3, 1, 1, datetime('now', '-7 days'))")


conn.commit()
cursor.close()
conn.close()

print("✅ Database 'vaccinedatabase.db' initialized successfully with enhanced schema and sample data.")
