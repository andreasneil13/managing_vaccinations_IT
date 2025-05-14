# Vaccination Management System - Main Page (Base Class)
import tkinter as tk
from tkinter import ttk, Listbox, Scrollbar, Frame, Label, messagebox, END
import sqlite3

class MainPage:
    """
    Base class for the main pages of different user roles.
    Provides a common structure, including a list of available vaccines.
    """
    def __init__(self, user_type_display_name, current_user_id, current_user_role):
        """
        Initializes the main page window.
        Args:
            user_type_display_name (str): The display name for the user role (e.g., "Doctor", "Patient").
            current_user_id (int): The ID of the currently logged-in user (from Person table).
            current_user_role (str): The role of the currently logged-in user (e.g., "doctor", "patient").
        """
        self.root = tk.Tk()
        self.root.title(f"Vaccination System - {user_type_display_name} Dashboard")
        self.root.geometry("800x600") # Adjusted default size
        self.root.configure(bg='#f0f8ff') # Light AliceBlue background

        self.current_user_id = current_user_id # This is the person_id
        self.current_user_role = current_user_role
        self.specific_role_id = self.get_specific_role_id() # e.g., doctor_id, patient_id

        # --- Common Header ---
        header_frame = Frame(self.root, bg='#4682b4', pady=10) # SteelBlue header
        header_frame.pack(fill=tk.X)
        Label(header_frame, text=f"{user_type_display_name} Dashboard", font=("Arial", 16, "bold"), fg='white', bg='#4682b4').pack()

        # --- Main Content Frame ---
        # This frame will be used by subclasses to add their specific widgets
        self.main_content_frame = Frame(self.root, bg='#f0f8ff', padx=20, pady=20)
        self.main_content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Common: Vaccine List Display (Optional for some roles, but good to have in base) ---
        # Subclasses can decide whether to call create_vaccine_list_display
        # self.create_vaccine_list_display() # Example: call if needed

        # --- Footer ---
        footer_frame = Frame(self.root, bg='#4682b4', pady=5) # SteelBlue footer
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = Label(footer_frame, text="Status: Ready", fg='white', bg='#4682b4', anchor=tk.W)
        self.status_label.pack(fill=tk.X, padx=10)


    def get_specific_role_id(self):
        """
        Fetches the specific role ID (e.g., doctor_id, patient_id) based on person_id and role.
        Returns:
            int or None: The specific role ID if found, otherwise None.
        """
        if not self.current_user_id or not self.current_user_role:
            return None

        db_path = "vaccinedatabase.db"
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            table_map = {
                "doctor": "Doctor",
                "patient": "Patient",
                "nurse": "Nurse",
                "center_admin": "CenterAdmin"
            }
            id_column_map = {
                "doctor": "iddoctor",
                "patient": "idpatient",
                "nurse": "idnurse",
                "center_admin": "idadmin"
            }
            if self.current_user_role in table_map:
                table_name = table_map[self.current_user_role]
                id_column = id_column_map[self.current_user_role]
                query = f"SELECT {id_column} FROM {table_name} WHERE idperson = ?"
                cursor.execute(query, (self.current_user_id,))
                result = cursor.fetchone()
                if result:
                    return result[0]
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to fetch role ID: {e}", parent=self.root)
            return None
        finally:
            if conn:
                conn.close()


    def create_vaccine_list_display(self, parent_frame, title="Available Vaccines"):
        """
        Creates and populates a listbox displaying available vaccines.
        Args:
            parent_frame (tk.Frame): The frame where the vaccine list will be placed.
            title (str): The title for the vaccine list section.
        """
        vaccine_frame = ttk.LabelFrame(parent_frame, text=title, padding=(10, 5))
        vaccine_frame.pack(pady=10, padx=5, fill=tk.X, expand=False) # Changed to not expand by default

        listbox_frame = Frame(vaccine_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = Scrollbar(listbox_frame, orient=tk.VERTICAL)
        self.vaccine_listbox = Listbox(listbox_frame, yscrollcommand=scrollbar.set, height=8, bg='#ffffff', selectbackground='#a6caf0')
        scrollbar.config(command=self.vaccine_listbox.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.vaccine_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.populate_vaccine_list()
        return self.vaccine_listbox # Return the listbox for binding events if needed

    def populate_vaccine_list(self):
        """Populates the vaccine listbox from the Medicine table."""
        if not hasattr(self, 'vaccine_listbox'): # Check if listbox exists
            return

        self.vaccine_listbox.delete(0, END)
        db_path = "vaccinedatabase.db"
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, Med_name FROM Medicine ORDER BY Med_name")
            vaccines = cursor.fetchall()
            if vaccines:
                for vaccine_id, med_name in vaccines:
                    self.vaccine_listbox.insert(END, f"{med_name} (ID: {vaccine_id})")
            else:
                self.vaccine_listbox.insert(END, "No vaccines listed in the database.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load vaccines: {e}", parent=self.root)
            self.vaccine_listbox.insert(END, "Error loading vaccines.")
        finally:
            if conn:
                conn.close()

    def run(self):
        """Starts the Tkinter main event loop for this window."""
        self.root.mainloop()

    def close_and_open_login(self):
        """Closes the current window and re-opens the login portal."""
        self.root.destroy()
        # This import is here to avoid circular dependency at the module level
        from login import LoginPortal # Re-import LoginPortal
        login_root = tk.Tk()
        LoginPortal(login_root) # Create a new instance of LoginPortal
        login_root.mainloop()

    def add_logout_button(self):
        """Adds a logout button to the main content frame."""
        logout_button = ttk.Button(self.main_content_frame, text="Logout", command=self.close_and_open_login, style="Accent.TButton")
        logout_button.pack(pady=20, side=tk.BOTTOM)

        # Style for the logout button
        style = ttk.Style(self.root)
        style.configure("Accent.TButton", foreground="white", background="red", font=('Arial', 10, 'bold'))


# Example of how a subclass might use it (for testing purposes)
if __name__ == "__main__":
    # This is just for testing MainPage directly.
    # In the actual application, subclasses (DoctorMainPage, PatientMainPage, etc.) will be instantiated.
    # We need to mock current_user_id and current_user_role for this test.
    # For a real run, these would come from the login process.

    # Mocking a user login for testing
    mock_person_id = 1 # Assuming person with ID 1 is a doctor
    mock_user_role = "doctor"

    # To get the specific role ID (e.g., iddoctor), we'd normally query the DB.
    # For this direct test, let's assume we know iddoctor for person_id 1 is 1.
    # The get_specific_role_id method in MainPage handles this.

    app = MainPage(user_type_display_name="Test User", current_user_id=mock_person_id, current_user_role=mock_user_role)
    
    # Example of adding a simple label to the main_content_frame
    Label(app.main_content_frame, text="This is the main content area.", font=("Arial", 12)).pack(pady=10)
    
    # Example of adding the vaccine list to the main_content_frame
    app.create_vaccine_list_display(app.main_content_frame, title="System Vaccines")
    
    app.add_logout_button()
    app.run()
