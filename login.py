# Vaccination Management System - Login Portal
import tkinter as tk
from tkinter import messagebox, ttk, Frame, Label, Entry, Button
import sqlite3
import re # For email validation
import os
# Import specific main page classes (will be defined in their respective files)
from patient_main_page import PatientMainPage
from doctor_main_page import DoctorMainPage
from nurse_main_page import NurseMainPage
from center_admin_main_page import CenterAdminMainPage

DB_PATH = 'vaccinedatabase.db'

class LoginPortal:
    def __init__(self, root):
        self.root = root
        self.root.title("Vaccination System Login")
        self.root.geometry("450x550") # Adjusted size for better layout
        self.root.configure(bg='#e0f7fa') # Light cyan background

        # --- Styling ---
        self.style = ttk.Style()
        self.style.theme_use('clam') # Using a modern theme

        self.style.configure('TLabel', background='#e0f7fa', font=('Arial', 11))
        self.style.configure('Header.TLabel', background='#00796b', foreground='white', font=('Arial', 18, 'bold'), padding=10) # Teal header
        self.style.configure('TButton', font=('Arial', 11, 'bold'), padding=5)
        self.style.configure('Login.TButton', background='#00796b', foreground='white') # Teal button
        self.style.map('Login.TButton', background=[('active', '#004d40')]) # Darker teal on hover/press
        self.style.configure('Register.TButton', background='#fbc02d', foreground='black') # Amber button
        self.style.map('Register.TButton', background=[('active', '#f57f17')]) # Darker amber on hover/press
        self.style.configure('TEntry', font=('Arial', 11), padding=5)

        # --- Main Frame ---
        main_frame = ttk.Frame(root, padding="20 20 20 20", style='TFrame')
        main_frame.pack(expand=True, fill=tk.BOTH)
        self.style.configure('TFrame', background='#e0f7fa')


        # --- Title ---
        title_label = ttk.Label(main_frame, text="Vaccination Management System", style='Header.TLabel', anchor=tk.CENTER)
        title_label.pack(fill=tk.X, pady=(0, 20))

        # --- Login Section ---
        login_frame = ttk.LabelFrame(main_frame, text="User Login", padding="15 10", style='TLabelframe')
        login_frame.pack(pady=10, padx=10, fill=tk.X)
        self.style.configure('TLabelframe', background='#e0f7fa', bordercolor='#00796b')
        self.style.configure('TLabelframe.Label', background='#e0f7fa', foreground='#00796b', font=('Arial', 12, 'bold'))


        ttk.Label(login_frame, text="Email:").grid(row=0, column=0, padx=5, pady=8, sticky=tk.W)
        self.email_entry = ttk.Entry(login_frame, width=30)
        self.email_entry.grid(row=0, column=1, padx=5, pady=8, sticky=tk.EW)

        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=8, sticky=tk.W)
        self.password_entry = ttk.Entry(login_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, padx=5, pady=8, sticky=tk.EW)

        login_button = ttk.Button(login_frame, text="Login", command=self.login, style='Login.TButton')
        login_button.grid(row=2, column=0, columnspan=2, padx=5, pady=15, sticky=tk.EW)

        # --- Registration Button ---
        register_button = ttk.Button(main_frame, text="Register New User (Doctor, Nurse, Admin)",
                                     command=self.open_registration_window, style='Register.TButton')
        register_button.pack(pady=15, padx=10, fill=tk.X)
        
        # Make grid columns in login_frame responsive
        login_frame.grid_columnconfigure(1, weight=1)

    def validate_email(self, email):
        """Validates email format using a regular expression."""
        if not email: return False
        # Basic regex for email validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """Validates password (e.g., minimum length)."""
        if not password or len(password) < 6: # Example: min 6 characters
            messagebox.showerror("Validation Error", "Password must be at least 6 characters long.", parent=self.root)
            return False
        return True

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Login Error", "Please enter both email and password.", parent=self.root)
            return

        if not self.validate_email(email):
            messagebox.showerror("Login Error", "Invalid email format.", parent=self.root)
            return

        user_data = self.authenticate_user(email, password)
        if user_data:
            person_id = user_data['person_id']
            user_role = user_data['user_type']
            first_name = user_data['firstname']

            messagebox.showinfo("Login Successful", f"Welcome, {first_name}!", parent=self.root)
            self.root.destroy()  # Close the login window

            # Open the appropriate main page based on the user's role
            if user_role == "patient":
                PatientMainPage(current_user_id=person_id, current_user_role=user_role).run()
            elif user_role == "doctor":
                DoctorMainPage(current_user_id=person_id, current_user_role=user_role).run()
            elif user_role == "nurse":
                NurseMainPage(current_user_id=person_id, current_user_role=user_role).run()
            elif user_role == "center_admin":
                CenterAdminMainPage(current_user_id=person_id, current_user_role=user_role).run()
            else:
                # Fallback if role is unknown, though DB constraints should prevent this
                messagebox.showerror("Role Error", f"Unknown user role: {user_role}")
                self.reopen_login_portal() # Re-open login if role is problematic
        else:
            messagebox.showerror("Login Failed", "Incorrect email or password.", parent=self.root)

    def authenticate_user(self, email, password):
        """Authenticates user against the database."""
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row # Access columns by name
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.person_id, c.user_type, p.firstname
                FROM Credentials c
                JOIN Person p ON c.person_id = p.idperson
                WHERE c.email = ? AND c.password = ?
            """, (email, password))
            user_row = cursor.fetchone()
            if user_row:
                return dict(user_row) # Convert row object to dictionary
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Authentication failed: {e}", parent=self.root)
            return None
        finally:
            if conn:
                conn.close()

    def open_registration_window(self):
        self.registration_window = tk.Toplevel(self.root)
        self.registration_window.title("User Registration")
        self.registration_window.geometry("450x450")
        self.registration_window.configure(bg='#e0f7fa')
        self.registration_window.transient(self.root) # Keep on top of login
        self.registration_window.grab_set() # Modal behavior

        reg_main_frame = ttk.Frame(self.registration_window, padding="20", style='TFrame')
        reg_main_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(reg_main_frame, text="Register New Staff", font=('Arial', 16, 'bold'), foreground='#00796b').pack(pady=(0,15))

        fields = ["First Name:", "Last Name:", "Date of Birth (YYYY-MM-DD):", "Email:", "Password:", "Confirm Password:", "User Type:"]
        self.reg_entries = {}

        for i, field in enumerate(fields):
            ttk.Label(reg_main_frame, text=field).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            if field == "User Type:":
                self.reg_entries[field] = ttk.Combobox(reg_main_frame, values=["doctor", "nurse", "center_admin"], state="readonly", width=28)
                self.reg_entries[field].set("doctor") # Default selection
            elif field == "Password:" or field == "Confirm Password:":
                 self.reg_entries[field] = ttk.Entry(reg_main_frame, show="*", width=30)
            else:
                self.reg_entries[field] = ttk.Entry(reg_main_frame, width=30)
            self.reg_entries[field].grid(row=i, column=1, padx=5, pady=5, sticky=tk.EW)

        reg_main_frame.grid_columnconfigure(1, weight=1)

        register_btn = ttk.Button(reg_main_frame, text="Register", command=self.register_user, style='Login.TButton')
        register_btn.grid(row=len(fields), column=0, columnspan=2, padx=5, pady=20, sticky=tk.EW)

    def register_user(self):
        # Retrieve data from registration form
        first_name = self.reg_entries["First Name:"].get()
        last_name = self.reg_entries["Last Name:"].get()
        dob = self.reg_entries["Date of Birth (YYYY-MM-DD):"].get() # TODO: Add date validation
        email = self.reg_entries["Email:"].get()
        password = self.reg_entries["Password:"].get()
        confirm_password = self.reg_entries["Confirm Password:"].get()
        user_type = self.reg_entries["User Type:"].get()

        # --- Validations ---
        if not all([first_name, last_name, dob, email, password, confirm_password, user_type]):
            messagebox.showerror("Error", "All fields are required.", parent=self.registration_window)
            return

        if not self.validate_email(email):
            messagebox.showerror("Error", "Invalid email format.", parent=self.registration_window)
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match.", parent=self.registration_window)
            return

        if not self.validate_password(password): # Uses the password validation from login
            # Messagebox is shown by validate_password itself
            return

        # Validate DOB format (basic check)
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
            messagebox.showerror("Error", "Invalid Date of Birth format. Please use YYYY-MM-DD.", parent=self.registration_window)
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute("SELECT email FROM Credentials WHERE email = ?", (email,))
            if cursor.fetchone():
                messagebox.showerror("Error", "This email is already registered.", parent=self.registration_window)
                return

            # Insert into Person table
            cursor.execute("INSERT INTO Person (firstname, familyname, dateofbirth) VALUES (?, ?, ?)",
                           (first_name, last_name, dob))
            person_id = cursor.lastrowid # Get the ID of the newly inserted person

            # Insert into the specific role table (Doctor, Nurse, CenterAdmin)
            role_table_map = {
                "doctor": "Doctor",
                "nurse": "Nurse",
                "center_admin": "CenterAdmin"
            }
            if user_type in role_table_map:
                role_table_name = role_table_map[user_type]
                cursor.execute(f"INSERT INTO {role_table_name} (idperson) VALUES (?)", (person_id,))
            else:
                messagebox.showerror("Error", "Invalid user type selected.", parent=self.registration_window)
                conn.rollback() # Rollback person insertion if role is invalid
                return

            # Insert into Credentials table
            cursor.execute("INSERT INTO Credentials (email, password, user_type, person_id) VALUES (?, ?, ?, ?)",
                           (email, password, user_type, person_id))

            conn.commit()
            messagebox.showinfo("Success", "Registration successful! You can now log in.", parent=self.registration_window)
            self.registration_window.destroy()

        except sqlite3.IntegrityError as ie:
            # This might happen if person_id is not unique in role tables (should be handled by UNIQUE constraint)
            messagebox.showerror("Database Error", f"Registration failed due to a data conflict: {ie}. The email might already be in use.", parent=self.registration_window)
            if conn: conn.rollback()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Registration failed: {e}", parent=self.registration_window)
            if conn: conn.rollback()
        finally:
            if conn:
                conn.close()

    def reopen_login_portal(self):
        """Helper to reopen the login portal if something goes wrong after closing it."""
        new_root = tk.Tk()
        LoginPortal(new_root)
        new_root.mainloop()


def main():
    # Initialize and run the database setup script first if it's not already done
    # import database # You might run database.py separately once
    
    root = tk.Tk()
    app = LoginPortal(root)
    root.mainloop()

if __name__ == "__main__":
    # It's good practice to ensure the database exists and has tables.
    # Running database.py manually once or having a check here is advisable.
    if not os.path.exists(DB_PATH):
        messagebox.showerror("Database Error", f"Database file '{DB_PATH}' not found. Please run database.py first.")
    else:
        # Check if essential tables exist
        conn_check = None
        try:
            conn_check = sqlite3.connect(DB_PATH)
            cursor_check = conn_check.cursor()
            cursor_check.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Credentials';")
            if not cursor_check.fetchone():
                messagebox.showerror("Database Error", "Table 'Credentials' not found. The database might be corrupted or not initialized correctly. Please run database.py.")
            else:
                main() # Proceed to login if DB and table exist
        except sqlite3.Error as e:
             messagebox.showerror("Database Error", f"Error connecting to database: {e}")
        finally:
            if conn_check:
                conn_check.close()

