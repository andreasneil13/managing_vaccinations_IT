# patient_main_page.py – Vaccination System
import tkinter as tk
from tkinter import ttk, messagebox, Frame, Label, Listbox, Scrollbar, END, Toplevel, Text
import sqlite3
from main_page import MainPage # Base class
import os
DB_PATH = 'vaccinedatabase.db'

class PatientMainPage(MainPage):
    def __init__(self, current_user_id, current_user_role):
        super().__init__(user_type_display_name="Patient", current_user_id=current_user_id, current_user_role=current_user_role)
        # self.patient_id is now self.specific_role_id from MainPage
        if self.specific_role_id is None:
             messagebox.showerror("Error", "Patient ID not found. Cannot load Patient dashboard.", parent=self.root)
             self.root.destroy()
             return

        self._setup_patient_ui()
        self.add_logout_button()

    def _setup_patient_ui(self):
        """Sets up the UI elements specific to the Patient's dashboard."""
        action_frame = ttk.LabelFrame(self.main_content_frame, text="Your Vaccine Information", padding=(15,10))
        action_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Button to View New/Pending Prescriptions
        ttk.Button(action_frame, text="View My New Prescriptions", command=self.view_new_prescriptions).pack(pady=8, fill=tk.X)

        # Button to View Vaccination History
        ttk.Button(action_frame, text="View My Vaccination History", command=self.view_vaccination_history).pack(pady=8, fill=tk.X)

        # Button to Check Vaccine Availability (for pending prescriptions)
        ttk.Button(action_frame, text="Check Availability for My Prescribed Vaccines", command=self.check_vaccine_availability).pack(pady=8, fill=tk.X)

        # Optional: Display general list of all vaccines (can be useful for patient awareness)
        # self.create_vaccine_list_display(self.main_content_frame, title="All Available Vaccines in System")


    def _display_data_in_new_window(self, title, data_fetch_function, *args):
        """
        Helper function to display data in a new Toplevel window with a Listbox.
        Args:
            title (str): The title of the Toplevel window.
            data_fetch_function (callable): A function that fetches and formats the data.
                                           It should return a list of strings to display.
            *args: Arguments to pass to the data_fetch_function.
        """
        display_window = Toplevel(self.root)
        display_window.title(title)
        display_window.geometry("600x400")
        display_window.configure(bg='#e0f7fa')
        display_window.transient(self.root)
        display_window.grab_set()

        frame = ttk.Frame(display_window, padding=10)
        frame.pack(expand=True, fill=tk.BOTH)

        Label(frame, text=title, font=("Arial", 14, "bold"), background='#e0f7fa', foreground='#00796b').pack(pady=(0,10))

        list_frame = Frame(frame)
        list_frame.pack(expand=True, fill=tk.BOTH)

        scrollbar = Scrollbar(list_frame, orient=tk.VERTICAL)
        listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, height=15, bg="white", selectbackground="#a6caf0", font=("Arial", 10))
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            items = data_fetch_function(conn, *args)
            if items:
                for item in items:
                    listbox.insert(END, item)
            else:
                listbox.insert(END, "No information available.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load data: {e}", parent=display_window)
            listbox.insert(END, "Error loading data.")
        except Exception as ex: # Catch other potential errors from data_fetch_function
            messagebox.showerror("Application Error", f"An error occurred: {ex}", parent=display_window)
            listbox.insert(END, "Error processing data.")
        finally:
            if conn:
                conn.close()

    def _fetch_new_prescriptions(self, conn, patient_id):
        """Fetches new/pending prescriptions for the patient."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.Med_name, pr.quantity, pr.prescription_date, p_doc.familyname AS doctor_name
            FROM Prescription pr
            JOIN Medicine m ON pr.id_medicine = m.id
            JOIN Doctor doc ON pr.iddoctor = doc.iddoctor
            JOIN Person p_doc ON doc.idperson = p_doc.idperson
            WHERE pr.idpatient = ? AND pr.status = 'pending'
            ORDER BY pr.prescription_date DESC
        """, (patient_id,))
        prescriptions = cursor.fetchall()
        return [f"{row[0]} (Qty: {row[1]}) - Prescribed by Dr. {row[3]} on {row[2]}" for row in prescriptions] if prescriptions else ["No new prescriptions found."]

    def view_new_prescriptions(self):
        """Displays new/pending prescriptions for the logged-in patient."""
        self._display_data_in_new_window("My New Prescriptions",
                                         self._fetch_new_prescriptions,
                                         self.specific_role_id) # specific_role_id is patient_id

    def _fetch_vaccination_history(self, conn, patient_id):
        """Fetches the vaccination history for the patient."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.Med_name, pr.quantity, al.administered_at, vc.name AS center_name, p_nurse.familyname AS nurse_name
            FROM AdministrationLog al
            JOIN Prescription pr ON al.prescription_id = pr.id_prescription
            JOIN Medicine m ON pr.id_medicine = m.id
            JOIN Nurse n ON al.nurse_id = n.idnurse
            JOIN Person p_nurse ON n.idperson = p_nurse.idperson
            JOIN VaccinationCenter vc ON al.center_id = vc.idcenter
            WHERE pr.idpatient = ? AND pr.status = 'administered'
            ORDER BY al.administered_at DESC
        """, (patient_id,))
        history = cursor.fetchall()
        return [f"{row[0]} (Qty: {row[1]}) - Administered on {row[2]} at {row[3]} by Nurse {row[4]}" for row in history] if history else ["No vaccination history found."]

    def view_vaccination_history(self):
        """Displays the vaccination history for the logged-in patient."""
        self._display_data_in_new_window("My Vaccination History",
                                         self._fetch_vaccination_history,
                                         self.specific_role_id) # specific_role_id is patient_id

    def _fetch_vaccine_availability(self, conn, patient_id):
        """
        Fetches availability of vaccines for the patient's PENDING prescriptions.
        """
        cursor = conn.cursor()
        # Get pending prescriptions for the patient
        cursor.execute("""
            SELECT DISTINCT m.id AS vaccine_id, m.Med_name
            FROM Prescription pr
            JOIN Medicine m ON pr.id_medicine = m.id
            WHERE pr.idpatient = ? AND pr.status = 'pending'
        """, (patient_id,))
        pending_vaccines = cursor.fetchall()

        if not pending_vaccines:
            return ["No pending prescriptions to check availability for."]

        availability_info = []
        for vaccine_id, vaccine_name in pending_vaccines:
            availability_info.append(f"--- {vaccine_name} ---")
            cursor.execute("""
                SELECT vc.name AS center_name, cs.quantity
                FROM CenterStock cs
                JOIN VaccinationCenter vc ON cs.center_id = vc.idcenter
                WHERE cs.vaccine_id = ? AND cs.quantity > 0
                ORDER BY vc.name
            """, (vaccine_id,))
            centers = cursor.fetchall()
            if centers:
                for center_name, quantity in centers:
                    availability_info.append(f"  Available at: {center_name} (Stock: {quantity})")
            else:
                availability_info.append(f"  Currently not in stock at any listed center.")
            availability_info.append("") # Add a blank line for readability

        return availability_info if availability_info else ["Could not retrieve availability information."]


    def check_vaccine_availability(self):
        """Displays where pending prescribed vaccines are available."""
        self._display_data_in_new_window("Vaccine Availability for My Prescriptions",
                                         self._fetch_vaccine_availability,
                                         self.specific_role_id) # specific_role_id is patient_id


# This is for standalone testing of the PatientMainPage
if __name__ == "__main__":
    # Ensure the database exists and is populated. Run database.py first.
    # For testing, we need a valid person_id for a patient from the database.
    # Let's assume person_id 3 is 'patient1@example.com' (Robert Patient)
    mock_patient_person_id = 3
    mock_patient_role = "patient"

    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' not found. Please run database.py to create and populate it.")
    else:
        conn_test = None
        try:
            conn_test = sqlite3.connect(DB_PATH)
            cursor_test = conn_test.cursor()
            cursor_test.execute("SELECT person_id FROM Credentials WHERE person_id = ? AND user_type = 'patient'", (mock_patient_person_id,))
            if cursor_test.fetchone():
                app = PatientMainPage(current_user_id=mock_patient_person_id, current_user_role=mock_patient_role)
                app.run()
            else:
                print(f"Test patient with person_id {mock_patient_person_id} not found.")
                print("Please ensure 'database.py' has been run and contains this patient.")
        except sqlite3.Error as e:
            print(f"Database error during test setup: {e}")
        finally:
            if conn_test:
                conn_test.close()
