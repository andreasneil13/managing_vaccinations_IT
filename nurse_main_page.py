# nurse_main_page.py
import tkinter as tk
from tkinter import ttk, messagebox, Frame, Label, Listbox, Scrollbar, END, Toplevel, Text
import sqlite3
from main_page import MainPage # Base class
import os
DB_PATH = 'vaccinedatabase.db'

class NurseMainPage(MainPage):
    def __init__(self, current_user_id, current_user_role):
        super().__init__(user_type_display_name="Nurse", current_user_id=current_user_id, current_user_role=current_user_role)
        # self.nurse_id is now self.specific_role_id from MainPage
        if self.specific_role_id is None:
             messagebox.showerror("Error", "Nurse ID not found. Cannot load Nurse dashboard.", parent=self.root)
             self.root.destroy()
             return

        self.selected_patient_info = None # Stores {'name': display_name, 'idpatient': patient_id, 'idperson': person_id}
        self.selected_prescription_info = None # Stores {'id_prescription': id, 'vaccine_name': name, ...}
        
        self.patients_data = [] # To store patient details for combobox
        self.prescriptions_data = [] # To store prescription details for listbox

        self._setup_nurse_ui()
        self.add_logout_button()

    def _setup_nurse_ui(self):
        """Sets up the UI elements specific to the Nurse's dashboard."""
        # --- Patient Selection and Prescription Management Frame ---
        main_interaction_frame = ttk.LabelFrame(self.main_content_frame, text="Patient Vaccine Administration", padding=(15,10))
        main_interaction_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Patient Selection
        Label(main_interaction_frame, text="Select Patient:", font=("Arial", 10)).pack(anchor=tk.W, padx=5, pady=(5,0))
        self.patient_combobox = ttk.Combobox(main_interaction_frame, width=40, state="readonly", font=("Arial", 10))
        self.patient_combobox.pack(fill=tk.X, padx=5, pady=5)
        self.patient_combobox.bind("<<ComboboxSelected>>", self.on_patient_select)
        self.load_all_patients() # Nurses can typically see all patients for administration

        # Prescriptions List for Selected Patient
        Label(main_interaction_frame, text="Pending Prescriptions for Selected Patient:", font=("Arial", 10)).pack(anchor=tk.W, padx=5, pady=(10,0))
        
        prescription_list_frame = Frame(main_interaction_frame)
        prescription_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        pres_scrollbar = Scrollbar(prescription_list_frame, orient=tk.VERTICAL)
        self.prescription_listbox = Listbox(prescription_list_frame, yscrollcommand=pres_scrollbar.set, height=8, font=("Arial", 10), selectbackground="#a6caf0")
        pres_scrollbar.config(command=self.prescription_listbox.yview)
        pres_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.prescription_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.prescription_listbox.bind("<<ListboxSelect>>", self.on_prescription_select)

        # Administer Vaccine Button
        ttk.Button(main_interaction_frame, text="Administer Selected Vaccine", command=self.administer_vaccine, style="Accent.TButton").pack(pady=10, padx=5, fill=tk.X)
        
        # --- View Patient File Section (Similar to Doctor's) ---
        view_patient_frame = ttk.LabelFrame(self.main_content_frame, text="View Patient Records", padding=(10,5))
        view_patient_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        ttk.Button(view_patient_frame, text="View Selected Patient's File", command=self.view_patient_file_nurse).pack(pady=5, fill=tk.X)

        self.patient_file_display_nurse = tk.Text(view_patient_frame, height=8, width=80, wrap=tk.WORD, state=tk.DISABLED, bg="#f5f5f5", font=("Arial", 9))
        self.patient_file_display_nurse.pack(pady=5, fill=tk.BOTH, expand=True)
        
        patient_file_scrollbar = ttk.Scrollbar(view_patient_frame, orient=tk.VERTICAL, command=self.patient_file_display_nurse.yview)
        patient_file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=self.patient_file_display_nurse)
        self.patient_file_display_nurse.config(yscrollcommand=patient_file_scrollbar.set)


    def load_all_patients(self):
        """Populates the combobox with all patients in the system."""
        self.patient_combobox.set('')
        self.patient_combobox['values'] = []
        self.patients_data = [] 

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT P.idpatient, Person.firstname, Person.familyname, Person.idperson
                FROM Patient P
                JOIN Person ON P.idperson = Person.idperson
                ORDER BY Person.familyname, Person.firstname
            """)
            patients = cursor.fetchall()
            if patients:
                patient_display_names = []
                for patient_id, first, last, person_id in patients:
                    display_name = f"{last}, {first} (ID: {patient_id})"
                    patient_display_names.append(display_name)
                    self.patients_data.append({'name': display_name, 'idpatient': patient_id, 'idperson': person_id})
                self.patient_combobox['values'] = patient_display_names
            else:
                self.patient_combobox['values'] = ["No patients found in system."]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load patients: {e}", parent=self.root)
            self.patient_combobox['values'] = ["Error loading patients."]
        finally:
            if conn:
                conn.close()

    def on_patient_select(self, event=None):
        """Handles patient selection and loads their pending prescriptions."""
        selected_display_name = self.patient_combobox.get()
        self.selected_prescription_info = None # Reset selected prescription
        self.prescription_listbox.delete(0, END) # Clear prescription list
        self.clear_patient_file_display_nurse() # Clear patient file display

        if selected_display_name and selected_display_name not in ["No patients found in system.", "Error loading patients."]:
            for patient_info in self.patients_data:
                if patient_info['name'] == selected_display_name:
                    self.selected_patient_info = patient_info
                    self.status_label.config(text=f"Selected Patient: {self.selected_patient_info['name']}")
                    self.load_pending_prescriptions_for_patient(self.selected_patient_info['idpatient'])
                    return
        self.selected_patient_info = None
        self.status_label.config(text="No patient selected.")


    def load_pending_prescriptions_for_patient(self, patient_id):
        """Loads pending prescriptions for the given patient ID into the listbox."""
        self.prescription_listbox.delete(0, END)
        self.prescriptions_data = []

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT pr.id_prescription, m.Med_name, pr.quantity, pr.prescription_date,
                       p_doc.familyname AS doctor_name, m.id AS medicine_id
                FROM Prescription pr
                JOIN Medicine m ON pr.id_medicine = m.id
                JOIN Doctor doc ON pr.iddoctor = doc.iddoctor
                JOIN Person p_doc ON doc.idperson = p_doc.idperson
                WHERE pr.idpatient = ? AND pr.status = 'pending'
                ORDER BY pr.prescription_date DESC
            """, (patient_id,))
            prescriptions = cursor.fetchall()
            if prescriptions:
                for pres_id, med_name, qty, pres_date, doc_name, med_id in prescriptions:
                    display_text = f"{med_name} (Qty: {qty}) - Prescribed by Dr. {doc_name} on {pres_date}"
                    self.prescription_listbox.insert(END, display_text)
                    self.prescriptions_data.append({
                        'id_prescription': pres_id,
                        'vaccine_name': med_name,
                        'vaccine_id': med_id, # Medicine.id
                        'quantity': qty,
                        'display_text': display_text
                    })
            else:
                self.prescription_listbox.insert(END, "No pending prescriptions for this patient.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load prescriptions: {e}", parent=self.root)
            self.prescription_listbox.insert(END, "Error loading prescriptions.")
        finally:
            if conn:
                conn.close()

    def on_prescription_select(self, event=None):
        """Handles prescription selection from the listbox."""
        selection = self.prescription_listbox.curselection()
        if selection:
            selected_index = selection[0]
            # Ensure the selected index is valid for prescriptions_data
            if 0 <= selected_index < len(self.prescriptions_data):
                self.selected_prescription_info = self.prescriptions_data[selected_index]
                self.status_label.config(text=f"Selected Prescription: {self.selected_prescription_info['vaccine_name']}")
                return
            else: # Index out of bounds, likely "No pending..." or "Error..." message was clicked
                self.selected_prescription_info = None
                self.status_label.config(text="Please select a valid prescription.")
                return

        self.selected_prescription_info = None
        # Do not change status if nothing valid is selected or list is empty.
        # Keep current patient status or "No patient selected."

    def administer_vaccine(self):
        """Administers the selected vaccine to the selected patient."""
        if not self.selected_patient_info:
            messagebox.showerror("Error", "Please select a patient first.", parent=self.root)
            return
        if not self.selected_prescription_info:
            messagebox.showerror("Error", "Please select a prescription to administer.", parent=self.root)
            return

        patient_name = self.selected_patient_info['name']
        vaccine_name = self.selected_prescription_info['vaccine_name']
        vaccine_id = self.selected_prescription_info['vaccine_id'] # Medicine.id
        prescription_id = self.selected_prescription_info['id_prescription']
        nurse_id = self.specific_role_id # This is Nurse.idnurse

        # Ask for confirmation
        confirm = messagebox.askyesno("Confirm Administration",
                                      f"Administer {vaccine_name} to {patient_name}?",
                                      parent=self.root)
        if not confirm:
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # 1. Find an available stock for this vaccine.
            # For simplicity, let's assume the nurse administers from any center that has stock.
            # A more complex system might link nurses to specific centers or ask for center selection.
            cursor.execute("""
                SELECT cs.id AS stock_id, cs.center_id, cs.quantity
                FROM CenterStock cs
                WHERE cs.vaccine_id = ? AND cs.quantity > 0
                ORDER BY cs.quantity DESC -- Pick from center with most stock, or any other logic
                LIMIT 1 
            """, (vaccine_id,))
            stock_info = cursor.fetchone()

            if not stock_info:
                messagebox.showerror("Stock Error", f"No available stock found for {vaccine_name} in any center.", parent=self.root)
                return
            
            stock_id, center_id_for_administration, current_stock_quantity = stock_info

            # Start transaction
            conn.execute("BEGIN TRANSACTION")

            # 2. Update Prescription status to 'administered'
            cursor.execute("UPDATE Prescription SET status = 'administered' WHERE id_prescription = ?", (prescription_id,))

            # 3. Decrement stock in CenterStock
            cursor.execute("UPDATE CenterStock SET quantity = quantity - 1 WHERE id = ?", (stock_id,))
            
            # 4. Log the administration in AdministrationLog
            cursor.execute("""
                INSERT INTO AdministrationLog (prescription_id, nurse_id, center_id, administered_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (prescription_id, nurse_id, center_id_for_administration, ))

            conn.commit()
            messagebox.showinfo("Success", f"{vaccine_name} administered successfully to {patient_name}.", parent=self.root)
            
            # Refresh the prescription list for the current patient
            self.load_pending_prescriptions_for_patient(self.selected_patient_info['idpatient'])
            self.selected_prescription_info = None # Clear selection
            self.status_label.config(text=f"Administered {vaccine_name} to {patient_name}.")
            # Optionally, refresh patient file if it's currently displayed
            if self.patient_file_display_nurse.get("1.0", tk.END).strip():
                self.view_patient_file_nurse()


        except sqlite3.Error as e:
            if conn: conn.rollback()
            messagebox.showerror("Database Error", f"Failed to administer vaccine: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()

    def view_patient_file_nurse(self):
        """Displays the selected patient's file (details, prescriptions, history) in the nurse's UI."""
        if not self.selected_patient_info:
            messagebox.showinfo("Info", "Please select a patient to view their file.", parent=self.root)
            self.clear_patient_file_display_nurse()
            return

        patient_id = self.selected_patient_info['idpatient'] 
        patient_person_id = self.selected_patient_info['idperson']
        
        display_widget = self.patient_file_display_nurse
        display_widget.config(state=tk.NORMAL)
        display_widget.delete("1.0", tk.END)

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Fetch Patient Details
            cursor.execute("""
                SELECT p.firstname, p.familyname, p.dateofbirth, c.email
                FROM Person p
                LEFT JOIN Credentials c ON p.idperson = c.person_id /* Use LEFT JOIN in case credentials somehow missing */
                WHERE p.idperson = ?
            """, (patient_person_id,))
            details = cursor.fetchone()

            if details:
                display_widget.insert(tk.END, f"--- Patient Details ---\n", "header_nurse")
                display_widget.insert(tk.END, f"Name: {details[0] or 'N/A'} {details[1] or 'N/A'}\n")
                display_widget.insert(tk.END, f"DOB: {details[2] or 'N/A'}\n")
                display_widget.insert(tk.END, f"Email: {details[3] or 'N/A'}\n\n")

            # Fetch All Prescriptions (Pending and Administered)
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

            display_widget.insert(tk.END, "--- All Vaccine Prescriptions ---\n", "header_nurse")
            if prescriptions:
                for med_name, qty, status, pres_date, doc_name in prescriptions:
                    display_widget.insert(tk.END, f"- {med_name} (Qty: {qty}) | Status: {status.upper()} | Prescribed: {pres_date} by Dr. {doc_name}\n")
            else:
                display_widget.insert(tk.END, "No prescriptions found for this patient.\n")
            display_widget.insert(tk.END, "\n")

            # Fetch Vaccination History (from AdministrationLog)
            cursor.execute("""
                SELECT m.Med_name, pr.quantity, al.administered_at, vc.name AS center_name, n_person.familyname AS admin_nurse_name
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

            display_widget.insert(tk.END, "--- Vaccination History ---\n", "header_nurse")
            if history:
                for med_name, qty, admin_date, center, admin_nurse in history:
                    display_widget.insert(tk.END, f"- {med_name} (Qty: {qty}) | Administered: {admin_date} at {center} by Nurse {admin_nurse}\n")
            else:
                display_widget.insert(tk.END, "No vaccination history found for this patient.\n")

            display_widget.tag_configure("header_nurse", font=("Arial", 10, "bold", "underline"), foreground="#005b96")

        except sqlite3.Error as e:
            display_widget.insert(tk.END, f"Error loading patient file: {e}")
            messagebox.showerror("Database Error", f"Could not load patient file: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()
            display_widget.config(state=tk.DISABLED)

    def clear_patient_file_display_nurse(self):
        self.patient_file_display_nurse.config(state=tk.NORMAL)
        self.patient_file_display_nurse.delete("1.0", tk.END)
        self.patient_file_display_nurse.config(state=tk.DISABLED)


# This is for standalone testing of the NurseMainPage
if __name__ == "__main__":
    # Ensure the database exists and is populated. Run database.py first.
    # For testing, we need a valid person_id for a nurse from the database.
    # Let's assume person_id 5 is 'nurse1@example.com' (Michael Nurse)
    mock_nurse_person_id = 5
    mock_nurse_role = "nurse"
    
    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' not found. Please run database.py to create and populate it.")
    else:
        conn_test = None
        try:
            conn_test = sqlite3.connect(DB_PATH)
            cursor_test = conn_test.cursor()
            cursor_test.execute("SELECT person_id FROM Credentials WHERE person_id = ? AND user_type = 'nurse'", (mock_nurse_person_id,))
            if cursor_test.fetchone():
                app = NurseMainPage(current_user_id=mock_nurse_person_id, current_user_role=mock_nurse_role)
                app.run()
            else:
                print(f"Test nurse with person_id {mock_nurse_person_id} not found.")
                print("Please ensure 'database.py' has been run and contains this nurse.")
        except sqlite3.Error as e:
            print(f"Database error during test setup: {e}")
        finally:
            if conn_test:
                conn_test.close()
