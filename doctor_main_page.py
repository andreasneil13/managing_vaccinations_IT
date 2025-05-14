# doctor_main_page.py – Vaccination System
import tkinter as tk
from tkinter import ttk, messagebox, Frame, Label, Entry, Button, Listbox, Scrollbar, END, Toplevel
import sqlite3
import re # For email validation
from main_page import MainPage # Base class
import os
DB_PATH = 'vaccinedatabase.db'

class DoctorMainPage(MainPage):
    def __init__(self, current_user_id, current_user_role):
        super().__init__(user_type_display_name="Doctor", current_user_id=current_user_id, current_user_role=current_user_role)
        # self.doctor_id is now self.specific_role_id from MainPage
        if self.specific_role_id is None:
             messagebox.showerror("Error", "Doctor ID not found. Cannot load Doctor dashboard.", parent=self.root)
             self.root.destroy()
             return

        self.selected_patient_info = None  # To store (patient_display_name, patient_id)
        self.selected_vaccine_info = None # To store (vaccine_name, vaccine_id from Medicine table)

        self._setup_doctor_ui()
        self.add_logout_button() # Add logout button from base class

    def _setup_doctor_ui(self):
        """Sets up the UI elements specific to the Doctor's dashboard."""
        controls_frame = ttk.Frame(self.main_content_frame)
        controls_frame.pack(pady=10, padx=10, fill=tk.X)

        # --- Patient Management Section ---
        patient_mgmt_frame = ttk.LabelFrame(controls_frame, text="Patient Management", padding=(10,5))
        patient_mgmt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,10))

        # Patient selection
        Label(patient_mgmt_frame, text="Select Patient:").pack(pady=(5,0), anchor=tk.W)
        self.patients_combobox = ttk.Combobox(patient_mgmt_frame, width=35, state="readonly")
        self.patients_combobox.pack(pady=5, fill=tk.X)
        self.patients_combobox.bind("<<ComboboxSelected>>", self.on_patient_select)
        self.populate_patients_list() # Load doctor's patients

        # Register New Patient Button
        ttk.Button(patient_mgmt_frame, text="Register New Patient", command=self.open_patient_registration_window).pack(pady=10, fill=tk.X)

        # --- Vaccine Prescription Section ---
        vaccine_mgmt_frame = ttk.LabelFrame(controls_frame, text="Vaccine Prescription", padding=(10,5))
        vaccine_mgmt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Vaccine list (using the method from MainPage)
        self.vaccine_listbox = self.create_vaccine_list_display(vaccine_mgmt_frame, title="Select Vaccine to Prescribe")
        if self.vaccine_listbox: # Check if listbox was created
            self.vaccine_listbox.bind("<<ListboxSelect>>", self.on_vaccine_select_for_prescription)

        # Quantity Entry
        Label(vaccine_mgmt_frame, text="Quantity:").pack(pady=(5,0), anchor=tk.W)
        self.quantity_var = tk.StringVar(value="1") # Default quantity to 1
        self.quantity_entry = ttk.Entry(vaccine_mgmt_frame, textvariable=self.quantity_var, width=5)
        self.quantity_entry.pack(pady=5, anchor=tk.W)

        # Prescribe Vaccine Button
        ttk.Button(vaccine_mgmt_frame, text="Prescribe Selected Vaccine", command=self.prescribe_vaccine).pack(pady=10, fill=tk.X)

        # --- View Patient File Section ---
        view_patient_frame = ttk.LabelFrame(self.main_content_frame, text="Patient Records", padding=(10,5))
        view_patient_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Button(view_patient_frame, text="View Selected Patient's File", command=self.view_patient_file).pack(pady=10, fill=tk.X)

        self.patient_file_display = tk.Text(view_patient_frame, height=10, width=80, wrap=tk.WORD, state=tk.DISABLED, bg="#f5f5f5")
        self.patient_file_display.pack(pady=5, fill=tk.BOTH, expand=True)
        
        # Scrollbar for patient file display
        patient_file_scrollbar = ttk.Scrollbar(view_patient_frame, orient=tk.VERTICAL, command=self.patient_file_display.yview)
        patient_file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.patient_file_display) # Pack before to ensure it's next to Text
        self.patient_file_display.config(yscrollcommand=patient_file_scrollbar.set)


    def populate_patients_list(self):
        """Populates the combobox with patients assigned to this doctor."""
        self.patients_combobox.set('') # Clear current selection
        self.patients_combobox['values'] = []
        self.patients_data = [] # Store (display_name, patient_id, person_id)

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Fetches patient's idpatient, firstname, familyname, and idperson
            cursor.execute("""
                SELECT P.idpatient, Person.firstname, Person.familyname, Person.idperson
                FROM Patient P
                JOIN Person ON P.idperson = Person.idperson
                JOIN DoctorPatient DP ON P.idpatient = DP.idpatient
                WHERE DP.iddoctor = ?
                ORDER BY Person.familyname, Person.firstname
            """, (self.specific_role_id,)) # Use specific_role_id which is doctor_id here
            
            patients = cursor.fetchall()
            if patients:
                patient_display_names = []
                for patient_id, first, last, person_id in patients:
                    display_name = f"{last}, {first} (ID: {patient_id})"
                    patient_display_names.append(display_name)
                    self.patients_data.append({'name': display_name, 'idpatient': patient_id, 'idperson': person_id})
                self.patients_combobox['values'] = patient_display_names
            else:
                self.patients_combobox['values'] = ["No patients assigned."]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load patients: {e}", parent=self.root)
            self.patients_combobox['values'] = ["Error loading patients."]
        finally:
            if conn:
                conn.close()

    def on_patient_select(self, event=None):
        """Handles patient selection from the combobox."""
        selected_display_name = self.patients_combobox.get()
        if selected_display_name and selected_display_name not in ["No patients assigned.", "Error loading patients."]:
            # Find the patient_id from self.patients_data
            for patient_info in self.patients_data:
                if patient_info['name'] == selected_display_name:
                    self.selected_patient_info = patient_info # Store full info
                    self.status_label.config(text=f"Selected Patient: {self.selected_patient_info['name']}")
                    self.clear_patient_file_display() # Clear previous patient's data
                    return
        self.selected_patient_info = None
        self.status_label.config(text="No patient selected.")
        self.clear_patient_file_display()


    def on_vaccine_select_for_prescription(self, event=None):
        """Handles vaccine selection from the listbox for prescription."""
        selection = self.vaccine_listbox.curselection()
        if selection:
            selected_item = self.vaccine_listbox.get(selection[0])
            # Extract vaccine name and ID, assuming format "Vaccine Name (ID: X)"
            match = re.search(r"(.*) \(ID: (\d+)\)", selected_item)
            if match:
                vaccine_name = match.group(1).strip()
                vaccine_id = int(match.group(2))
                self.selected_vaccine_info = {'name': vaccine_name, 'id': vaccine_id}
                self.status_label.config(text=f"Selected Vaccine: {vaccine_name}")
                return
        self.selected_vaccine_info = None
        self.status_label.config(text="No vaccine selected for prescription.")


    def prescribe_vaccine(self):
        """Prescribes the selected vaccine to the selected patient."""
        if not self.selected_patient_info:
            messagebox.showerror("Error", "Please select a patient first.", parent=self.root)
            return
        if not self.selected_vaccine_info:
            messagebox.showerror("Error", "Please select a vaccine from the list.", parent=self.root)
            return

        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be a positive integer.", parent=self.root)
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity entered.", parent=self.root)
            return

        patient_id = self.selected_patient_info['idpatient']
        vaccine_id = self.selected_vaccine_info['id']
        vaccine_name = self.selected_vaccine_info['name']
        doctor_id = self.specific_role_id # This is the iddoctor

        confirm = messagebox.askyesno("Confirm Prescription",
                                      f"Prescribe {quantity} dose(s) of {vaccine_name} to {self.selected_patient_info['name']}?",
                                      parent=self.root)
        if not confirm:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Prescription (idpatient, id_medicine, iddoctor, quantity, status, prescription_date)
                VALUES (?, ?, ?, ?, 'pending', date('now'))
            """, (patient_id, vaccine_id, doctor_id, quantity))
            conn.commit()
            messagebox.showinfo("Success", f"{vaccine_name} prescribed successfully to {self.selected_patient_info['name']}.", parent=self.root)
            self.status_label.config(text=f"Prescribed {vaccine_name} to {self.selected_patient_info['name']}.")
            # Optionally, refresh patient file if it's currently displayed
            if self.patient_file_display.get("1.0", tk.END).strip(): # Check if display has content
                self.view_patient_file()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to prescribe vaccine: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()

    def open_patient_registration_window(self):
        """Opens a new window for registering a new patient."""
        self.patient_reg_window = Toplevel(self.root)
        self.patient_reg_window.title("Register New Patient")
        self.patient_reg_window.geometry("400x350")
        self.patient_reg_window.configure(bg='#e0f7fa')
        self.patient_reg_window.transient(self.root)
        self.patient_reg_window.grab_set()

        reg_frame = ttk.Frame(self.patient_reg_window, padding="20")
        reg_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(reg_frame, text="Patient Registration Details", font=('Arial', 14, 'bold'), foreground='#00796b').grid(row=0, column=0, columnspan=2, pady=(0,15))

        fields = ["First Name:", "Last Name:", "Date of Birth (YYYY-MM-DD):", "Email:", "Password:"]
        self.patient_reg_entries = {}

        for i, field_text in enumerate(fields):
            ttk.Label(reg_frame, text=field_text).grid(row=i+1, column=0, padx=5, pady=5, sticky=tk.W)
            entry_widget = ttk.Entry(reg_frame, width=30, show="*" if field_text == "Password:" else "")
            entry_widget.grid(row=i+1, column=1, padx=5, pady=5, sticky=tk.EW)
            self.patient_reg_entries[field_text] = entry_widget
        
        reg_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(reg_frame, text="Register Patient", command=self.register_new_patient, style='Login.TButton').grid(row=len(fields)+1, column=0, columnspan=2, pady=20, sticky=tk.EW)

    def validate_email_format(self, email): # Copied from LoginPortal for direct use
        if not email: return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def register_new_patient(self):
        """Handles the logic for registering a new patient."""
        first_name = self.patient_reg_entries["First Name:"].get()
        last_name = self.patient_reg_entries["Last Name:"].get()
        dob = self.patient_reg_entries["Date of Birth (YYYY-MM-DD):"].get()
        email = self.patient_reg_entries["Email:"].get()
        password = self.patient_reg_entries["Password:"].get()

        if not all([first_name, last_name, dob, email, password]):
            messagebox.showerror("Error", "All fields are required.", parent=self.patient_reg_window)
            return

        if not self.validate_email_format(email): # Use the local validation method
            messagebox.showerror("Error", "Invalid email format.", parent=self.patient_reg_window)
            return
        
        if len(password) < 6: # Basic password length check
            messagebox.showerror("Error", "Password must be at least 6 characters long.", parent=self.patient_reg_window)
            return

        if not re.match(r"^\d{4}-\d{2}-\d{2}$", dob): # Basic DOB format check
            messagebox.showerror("Error", "Invalid Date of Birth format. Use YYYY-MM-DD.", parent=self.patient_reg_window)
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if email already exists in Credentials
            cursor.execute("SELECT email FROM Credentials WHERE email = ?", (email,))
            if cursor.fetchone():
                messagebox.showerror("Error", "This email is already registered.", parent=self.patient_reg_window)
                return

            # 1. Insert into Person table
            cursor.execute("INSERT INTO Person (firstname, familyname, dateofbirth) VALUES (?, ?, ?)",
                           (first_name, last_name, dob))
            person_id = cursor.lastrowid

            # 2. Insert into Patient table
            cursor.execute("INSERT INTO Patient (idperson) VALUES (?)", (person_id,))
            patient_id = cursor.lastrowid # This is the idpatient

            # 3. Insert into Credentials table for the patient
            cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES (?, ?, 'patient', ?)",
                           (email, password, person_id))

            # 4. Link patient to the current doctor in DoctorPatient table
            cursor.execute("INSERT INTO DoctorPatient (iddoctor, idpatient) VALUES (?, ?)",
                           (self.specific_role_id, patient_id)) # specific_role_id is doctor_id

            conn.commit()
            messagebox.showinfo("Success", f"Patient {first_name} {last_name} registered successfully and assigned to you.", parent=self.patient_reg_window)
            self.patient_reg_window.destroy()
            self.populate_patients_list() # Refresh the patient list in the main dashboard

        except sqlite3.IntegrityError as ie:
             messagebox.showerror("Database Error", f"Registration failed. The email might already exist or another data conflict occurred: {ie}", parent=self.patient_reg_window)
             if conn: conn.rollback()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to register patient: {e}", parent=self.patient_reg_window)
            if conn: conn.rollback()
        finally:
            if conn:
                conn.close()

    def view_patient_file(self):
        """Displays the selected patient's file (details, prescriptions, history)."""
        if not self.selected_patient_info:
            messagebox.showinfo("Info", "Please select a patient to view their file.", parent=self.root)
            self.clear_patient_file_display()
            return

        patient_id = self.selected_patient_info['idpatient'] # This is Patient.idpatient
        patient_person_id = self.selected_patient_info['idperson'] # This is Person.idperson for the patient
        
        self.patient_file_display.config(state=tk.NORMAL)
        self.patient_file_display.delete("1.0", tk.END)

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Fetch Patient Details
            cursor.execute("""
                SELECT p.firstname, p.familyname, p.dateofbirth, c.email
                FROM Person p
                JOIN Credentials c ON p.idperson = c.person_id
                WHERE p.idperson = ?
            """, (patient_person_id,))
            details = cursor.fetchone()

            if details:
                self.patient_file_display.insert(tk.END, f"--- Patient Details ---\n", "header")
                self.patient_file_display.insert(tk.END, f"Name: {details[0]} {details[1]}\n")
                self.patient_file_display.insert(tk.END, f"DOB: {details[2]}\n")
                self.patient_file_display.insert(tk.END, f"Email: {details[3]}\n\n")

            # Fetch Prescriptions (Pending and Administered)
            cursor.execute("""
                SELECT m.Med_name, pr.quantity, pr.status, pr.prescription_date, d_person.familyname AS doctor_name
                FROM Prescription pr
                JOIN Medicine m ON pr.id_medicine = m.id
                JOIN Doctor doc ON pr.iddoctor = doc.iddoctor
                JOIN Person d_person ON doc.idperson = d_person.idperson
                WHERE pr.idpatient = ?
                ORDER BY pr.prescription_date DESC
            """, (patient_id,))
            prescriptions = cursor.fetchall()

            self.patient_file_display.insert(tk.END, "--- Vaccine Prescriptions ---\n", "header")
            if prescriptions:
                for med_name, qty, status, pres_date, doc_name in prescriptions:
                    self.patient_file_display.insert(tk.END, f"- {med_name} (Qty: {qty}) | Status: {status.upper()} | Prescribed: {pres_date} by Dr. {doc_name}\n")
            else:
                self.patient_file_display.insert(tk.END, "No prescriptions found for this patient.\n")
            self.patient_file_display.insert(tk.END, "\n")

            # Fetch Vaccination History (from AdministrationLog)
            cursor.execute("""
                SELECT m.Med_name, pr.quantity, al.administered_at, vc.name AS center_name, n_person.familyname AS nurse_name
                FROM AdministrationLog al
                JOIN Prescription pr ON al.prescription_id = pr.id_prescription
                JOIN Medicine m ON pr.id_medicine = m.id
                JOIN Nurse n ON al.nurse_id = n.idnurse
                JOIN Person n_person ON n.idperson = n_person.idperson
                JOIN VaccinationCenter vc ON al.center_id = vc.idcenter
                WHERE pr.idpatient = ?
                ORDER BY al.administered_at DESC
            """, (patient_id,))
            history = cursor.fetchall()

            self.patient_file_display.insert(tk.END, "--- Vaccination History ---\n", "header")
            if history:
                for med_name, qty, admin_date, center, nurse in history:
                    self.patient_file_display.insert(tk.END, f"- {med_name} (Qty: {qty}) | Administered: {admin_date} at {center} by Nurse {nurse}\n")
            else:
                self.patient_file_display.insert(tk.END, "No vaccination history found for this patient.\n")

            # Configure tags for headers
            self.patient_file_display.tag_configure("header", font=("Arial", 11, "bold", "underline"), foreground="#005b96")

        except sqlite3.Error as e:
            self.patient_file_display.insert(tk.END, f"Error loading patient file: {e}")
            messagebox.showerror("Database Error", f"Could not load patient file: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()
            self.patient_file_display.config(state=tk.DISABLED)

    def clear_patient_file_display(self):
        self.patient_file_display.config(state=tk.NORMAL)
        self.patient_file_display.delete("1.0", tk.END)
        self.patient_file_display.config(state=tk.DISABLED)


# This is for standalone testing of the DoctorMainPage
if __name__ == "__main__":
    # Ensure the database exists and is populated. Run database.py first.
    # For testing, we need a valid person_id for a doctor from the database.
    # Let's assume person_id 1 is 'doc1@example.com' (John Doe)
    mock_doctor_person_id = 1 
    mock_doctor_role = "doctor"

    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' not found. Please run database.py to create and populate it.")
    else:
        # Verify if the mock doctor exists to prevent errors during testing
        conn_test = None
        try:
            conn_test = sqlite3.connect(DB_PATH)
            cursor_test = conn_test.cursor()
            cursor_test.execute("SELECT person_id FROM Credentials WHERE person_id = ? AND user_type = 'doctor'", (mock_doctor_person_id,))
            if cursor_test.fetchone():
                app = DoctorMainPage(current_user_id=mock_doctor_person_id, current_user_role=mock_doctor_role)
                app.run()
            else:
                print(f"Test doctor with person_id {mock_doctor_person_id} not found in the database.")
                print("Please ensure 'database.py' has been run and contains this doctor.")
        except sqlite3.Error as e:
            print(f"Database error during test setup: {e}")
        finally:
            if conn_test:
                conn_test.close()
