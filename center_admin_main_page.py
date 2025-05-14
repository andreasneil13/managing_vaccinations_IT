# center_admin_main_page.py
import tkinter as tk
# Import ttk widgets directly for clarity and to ensure ttk is used where intended
from tkinter import ttk, messagebox, Frame, Label, Entry, Button, Listbox, Scrollbar, END, Toplevel
import sqlite3
from main_page import MainPage # Base class
import os
DB_PATH = 'vaccinedatabase.db'

class CenterAdminMainPage(MainPage):
    def __init__(self, current_user_id, current_user_role):
        super().__init__(user_type_display_name="Center Administrator", current_user_id=current_user_id, current_user_role=current_user_role)
        # self.admin_id is self.specific_role_id (CenterAdmin.idadmin)
        if self.specific_role_id is None:
             messagebox.showerror("Error", "Admin ID not found. Cannot load Center Admin dashboard.", parent=self.root)
             self.root.destroy()
             return

        self.managed_center_id = None # VaccinationCenter.idcenter
        self.managed_center_name = None
        self.selected_vaccine_for_stock_info = None # Stores {'name': vaccine_name, 'id': vaccine_id}
        
        self.vaccines_data_for_stock = [] # Stores {'name': med_name, 'id': vaccine_id}

        self._setup_center_admin_ui()
        self.check_or_create_center_assignment()
        self.add_logout_button()

    def _setup_center_admin_ui(self):
        """Sets up the UI elements specific to the Center Admin's dashboard."""
        # Frame for center information and creation
        self.center_info_frame = ttk.LabelFrame(self.main_content_frame, text="My Vaccination Center", padding=(15,10))
        self.center_info_frame.pack(pady=10, padx=10, fill=tk.X)

        # FIX: Use ttk.Label inside ttk.LabelFrame. Remove the bg argument as ttk widgets handle background via themes.
        self.center_name_label = ttk.Label(self.center_info_frame, text="Managing: Not Assigned", font=("Arial", 12, "bold"))
        self.center_name_label.pack(pady=5)       
        self.register_center_button = ttk.Button(self.center_info_frame, text="Register/Assign My Center", command=self.open_center_registration_window)
        # This button will be packed later based on whether a center is assigned

        # Frame for stock management (initially might be disabled if no center)
        self.stock_management_frame = ttk.LabelFrame(self.main_content_frame, text="Vaccine Stock Management", padding=(15,10))
        self.stock_management_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Vaccine selection for stock update
        # Using ttk.Label for consistency inside ttk.LabelFrame
        ttk.Label(self.stock_management_frame, text="Select Vaccine:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.vaccine_stock_combobox = ttk.Combobox(self.stock_management_frame, width=40, state="readonly")
        self.vaccine_stock_combobox.pack(fill=tk.X, padx=5, pady=5)
        self.vaccine_stock_combobox.bind("<<ComboboxSelected>>", self.on_vaccine_select_for_stock)
        self.populate_all_vaccines_for_stock_combobox() # Load all system vaccines

        # Quantity Entry
        # Using ttk.Label for consistency inside ttk.LabelFrame
        ttk.Label(self.stock_management_frame, text="Quantity:").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.stock_quantity_var = tk.StringVar(value="10") # Default quantity
        self.stock_quantity_entry = ttk.Entry(self.stock_management_frame, textvariable=self.stock_quantity_var, width=10)
        self.stock_quantity_entry.pack(anchor=tk.W, padx=5, pady=5)

        # Add/Remove Stock Buttons
        buttons_frame = ttk.Frame(self.stock_management_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.add_stock_button = ttk.Button(buttons_frame, text="Add Stock", command=self.add_stock, style="Accent.TButton")
        self.add_stock_button.pack(side=tk.LEFT, padx=(0,5), expand=True, fill=tk.X)
        
        self.remove_stock_button = ttk.Button(buttons_frame, text="Remove Stock", command=self.remove_stock, style="Accent.TButton")
        # Applying a custom style, ensure 'self.style' is initialized in MainPage or before this.
        # Assuming MainPage initializes self.style = ttk.Style()
        try: # Use a try block in case style is not yet configured
             self.style.configure("Red.TButton", foreground="white", background="red", font=('Arial', 10, 'bold'))
             self.remove_stock_button.configure(style="Red.TButton") # Custom style for remove
        except AttributeError:
             # Fallback if self.style is not available or configured
             pass # Or configure a default style

        self.remove_stock_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Display current stock for selected vaccine
        # Using ttk.Label for consistency inside ttk.LabelFrame
        self.current_stock_label = ttk.Label(self.stock_management_frame, text="Current Stock for Selected Vaccine: N/A", font=("Arial", 10))
        self.current_stock_label.pack(anchor=tk.W, padx=5, pady=5)

        # Listbox to show all stock for the managed center
        # Using ttk.Label for consistency inside ttk.LabelFrame
        ttk.Label(self.stock_management_frame, text="Full Stock Overview for Your Center:", font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=5, pady=(15,0))
        stock_overview_frame = Frame(self.stock_management_frame) # Standard Frame is acceptable here
        stock_overview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        stock_scrollbar = Scrollbar(stock_overview_frame, orient=tk.VERTICAL) # Standard Scrollbar
        self.center_stock_listbox = Listbox(stock_overview_frame, yscrollcommand=stock_scrollbar.set, height=8, selectbackground="#a6caf0") # Standard Listbox
        stock_scrollbar.config(command=self.center_stock_listbox.yview)
        stock_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.center_stock_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.toggle_stock_management_active(False) # Initially disabled

    def toggle_stock_management_active(self, active=True):
        """Enables or disables stock management widgets."""
        state = tk.NORMAL if active else tk.DISABLED
        # Note: Combobox 'state' for readonly is special
        combo_state = "readonly" if active else tk.DISABLED

        self.vaccine_stock_combobox.config(state=combo_state) 
        self.stock_quantity_entry.config(state=state)
        self.add_stock_button.config(state=state)
        self.remove_stock_button.config(state=state)
        
        # Update status/info labels based on state
        if not active:
            # Use config method for ttk.Label as well
            self.current_stock_label.config(text="Current Stock for Selected Vaccine: N/A (No center assigned)")
            self.center_stock_listbox.delete(0, END)
            self.center_stock_listbox.insert(END, "Assign a center to manage stock.")
        else:
             # Reset label text when active, will be updated by subsequent calls
            self.current_stock_label.config(text="Current Stock for Selected Vaccine: N/A")
            # load_center_stock_overview will be called by check_or_create_center_assignment


    def check_or_create_center_assignment(self):
        """Checks if this admin is assigned to a center, or prompts for creation/assignment."""
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT idcenter, name FROM VaccinationCenter WHERE admin_id = ?", (self.specific_role_id,))
            center_data = cursor.fetchone()

            if center_data:
                self.managed_center_id = center_data[0]
                self.managed_center_name = center_data[1]
                # Use config method for ttk.Label
                self.center_name_label.config(text=f"Managing: {self.managed_center_name} (ID: {self.managed_center_id})")
                self.status_label.config(text=f"Managing center: {self.managed_center_name}")
                self.register_center_button.pack_forget() # Hide if already assigned
                self.toggle_stock_management_active(True)
                self.load_center_stock_overview()
            else:
                # Use config method for ttk.Label
                self.center_name_label.config(text="Managing: Not Assigned. Please register your center.")
                self.status_label.config(text="No center assigned. Please register one.")
                self.register_center_button.pack(pady=5) # Show button
                self.toggle_stock_management_active(False)
                # Prompt to register
                # messagebox.showinfo("Center Assignment", "You are not yet assigned to a vaccination center. Please register or select your center.", parent=self.root)
                # self.open_center_registration_window() # Optionally open it directly

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to check center assignment: {e}", parent=self.root)
            self.toggle_stock_management_active(False)
        finally:
            if conn:
                conn.close()

    def open_center_registration_window(self):
        """Opens a window to register a new center or assign an existing unmanaged one."""
        self.center_reg_window = Toplevel(self.root)
        self.center_reg_window.title("Register/Assign Vaccination Center")
        self.center_reg_window.geometry("450x300")
        self.center_reg_window.configure(bg='#e0f7fa') # Standard Toplevel supports bg
        self.center_reg_window.transient(self.root)
        self.center_reg_window.grab_set()

        reg_frame = ttk.Frame(self.center_reg_window, padding="20")
        reg_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(reg_frame, text="Center Details", font=('Arial', 14, 'bold'), foreground='#00796b').grid(row=0, column=0, columnspan=2, pady=(0,15))

        ttk.Label(reg_frame, text="Center Name:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.center_reg_name_entry = ttk.Entry(reg_frame, width=35)
        self.center_reg_name_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        ttk.Label(reg_frame, text="Address:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.center_reg_address_entry = ttk.Entry(reg_frame, width=35)
        self.center_reg_address_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        
        reg_frame.grid_columnconfigure(1, weight=1)

        # Ensure Login.TButton style is defined in MainPage or somewhere accessible
        ttk.Button(reg_frame, text="Register New Center & Assign to Me", command=self.register_new_center_and_assign, style='Login.TButton').grid(row=3, column=0, columnspan=2, pady=(15,5), sticky=tk.EW)
        
        # Option to assign an existing unmanaged center
        ttk.Label(reg_frame, text="Or Assign Existing Unmanaged Center:").grid(row=4, column=0, columnspan=2, pady=(10,0), sticky=tk.W)
        self.unmanaged_centers_combobox = ttk.Combobox(reg_frame, width=33, state="readonly")
        self.unmanaged_centers_combobox.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        self.load_unmanaged_centers()
        # Ensure Login.TButton style is defined
        ttk.Button(reg_frame, text="Assign Selected Center to Me", command=self.assign_existing_center, style='Login.TButton').grid(row=6, column=0, columnspan=2, pady=5, sticky=tk.EW)


    def load_unmanaged_centers(self):
        """Populates combobox with centers that have no admin_id."""
        self.unmanaged_centers_combobox.set('')
        self.unmanaged_centers_combobox['values'] = []
        self.unmanaged_centers_data = []

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT idcenter, name FROM VaccinationCenter WHERE admin_id IS NULL ORDER BY name")
            centers = cursor.fetchall()
            if centers:
                center_display_names = []
                for center_id, name in centers:
                    display_name = f"{name} (ID: {center_id})"
                    center_display_names.append(display_name)
                    self.unmanaged_centers_data.append({'name': display_name, 'idcenter': center_id})
                self.unmanaged_centers_combobox['values'] = center_display_names
            else:
                self.unmanaged_centers_combobox['values'] = ["No unmanaged centers available."]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load unmanaged centers: {e}", parent=self.center_reg_window)
        finally:
            if conn:
                conn.close()
    
    def assign_existing_center(self):
        selected_center_display = self.unmanaged_centers_combobox.get()
        if not selected_center_display or selected_center_display == "No unmanaged centers available.":
            messagebox.showerror("Error", "Please select an unmanaged center to assign.", parent=self.center_reg_window)
            return

        center_to_assign_id = None
        for center_info in self.unmanaged_centers_data:
            if center_info['name'] == selected_center_display:
                center_to_assign_id = center_info['idcenter']
                break
        
        if not center_to_assign_id:
            messagebox.showerror("Error", "Could not find selected center ID.", parent=self.center_reg_window)
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE VaccinationCenter SET admin_id = ? WHERE idcenter = ?", (self.specific_role_id, center_to_assign_id))
            conn.commit()
            messagebox.showinfo("Success", f"Center '{selected_center_display}' assigned to you successfully.", parent=self.center_reg_window)
            self.center_reg_window.destroy()
            self.check_or_create_center_assignment() # Refresh main dashboard
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to assign center: {e}", parent=self.center_reg_window)
        finally:
            if conn:
                conn.close()


    def register_new_center_and_assign(self):
        """Registers a new vaccination center and assigns current admin to it."""
        center_name = self.center_reg_name_entry.get()
        center_address = self.center_reg_address_entry.get()

        if not center_name or not center_address:
            messagebox.showerror("Error", "Center Name and Address are required.", parent=self.center_reg_window)
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Check if center name already exists
            cursor.execute("SELECT idcenter FROM VaccinationCenter WHERE name = ?", (center_name,))
            if cursor.fetchone():
                messagebox.showerror("Error", f"A center with the name '{center_name}' already exists.", parent=self.center_reg_window)
                return

            cursor.execute("INSERT INTO VaccinationCenter (name, address, admin_id) VALUES (?, ?, ?)",
                           (center_name, center_address, self.specific_role_id))
            conn.commit()
            messagebox.showinfo("Success", f"Center '{center_name}' registered and assigned to you successfully.", parent=self.center_reg_window)
            self.center_reg_window.destroy()
            self.check_or_create_center_assignment() # Refresh main dashboard

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to register center: {e}", parent=self.center_reg_window)
        finally:
            if conn:
                conn.close()

    def populate_all_vaccines_for_stock_combobox(self):
        """Populates the vaccine combobox for stock management from the Medicine table."""
        self.vaccine_stock_combobox.set('')
        self.vaccine_stock_combobox['values'] = []
        self.vaccines_data_for_stock = []

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, Med_name FROM Medicine ORDER BY Med_name")
            vaccines = cursor.fetchall()
            if vaccines:
                vaccine_display_names = []
                for vaccine_id, med_name in vaccines:
                    display_name = f"{med_name} (ID: {vaccine_id})"
                    vaccine_display_names.append(display_name)
                    self.vaccines_data_for_stock.append({'name': display_name, 'id': vaccine_id, 'med_name_only': med_name})
                self.vaccine_stock_combobox['values'] = vaccine_display_names
            else:
                self.vaccine_stock_combobox['values'] = ["No vaccines in system."]
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load vaccines for stock: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()

    def on_vaccine_select_for_stock(self, event=None):
        """Handles vaccine selection for stock management."""
        selected_display_name = self.vaccine_stock_combobox.get()
        self.selected_vaccine_for_stock_info = None
        # Use config method for ttk.Label
        self.current_stock_label.config(text="Current Stock for Selected Vaccine: N/A")

        if selected_display_name and selected_display_name != "No vaccines in system.":
            for vaccine_info in self.vaccines_data_for_stock:
                if vaccine_info['name'] == selected_display_name:
                    self.selected_vaccine_for_stock_info = vaccine_info
                    self.status_label.config(text=f"Selected for stock: {vaccine_info['med_name_only']}")
                    self.update_current_stock_display()
                    return
        self.status_label.config(text="No vaccine selected for stock.")

    def update_current_stock_display(self):
        """Updates the label showing current stock for the selected vaccine at the managed center."""
        if not self.managed_center_id or not self.selected_vaccine_for_stock_info:
            # Use config method for ttk.Label
            self.current_stock_label.config(text="Current Stock for Selected Vaccine: N/A")
            return

        vaccine_id = self.selected_vaccine_for_stock_info['id']
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM CenterStock WHERE center_id = ? AND vaccine_id = ?",
                           (self.managed_center_id, vaccine_id))
            result = cursor.fetchone()
            quantity = result[0] if result else 0
            # Use config method for ttk.Label
            self.current_stock_label.config(text=f"Current Stock for {self.selected_vaccine_for_stock_info['med_name_only']}: {quantity}")
        except sqlite3.Error as e:
            # Use config method for ttk.Label
            self.current_stock_label.config(text="Error fetching stock.")
            # messagebox.showerror("DB Error", f"Failed to fetch current stock: {e}", parent=self.root) # Can be noisy
        finally:
            if conn:
                conn.close()

    def _modify_stock(self, operation="add"):
        if not self.managed_center_id:
            messagebox.showerror("Error", "No vaccination center is assigned to you. Cannot modify stock.", parent=self.root)
            return
        if not self.selected_vaccine_for_stock_info:
            messagebox.showerror("Error", "Please select a vaccine to modify its stock.", parent=self.root)
            return

        try:
            quantity_change = int(self.stock_quantity_var.get())
            if quantity_change <= 0:
                messagebox.showerror("Error", "Quantity must be a positive integer.", parent=self.root)
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid quantity entered.", parent=self.root)
            return

        vaccine_id = self.selected_vaccine_for_stock_info['id']
        vaccine_name = self.selected_vaccine_for_stock_info['med_name_only']

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION")

            # Check current stock
            cursor.execute("SELECT id, quantity FROM CenterStock WHERE center_id = ? AND vaccine_id = ?",
                           (self.managed_center_id, vaccine_id))
            stock_entry = cursor.fetchone()

            if operation == "add":
                if stock_entry: # Update existing stock
                    new_quantity = stock_entry[1] + quantity_change
                    cursor.execute("UPDATE CenterStock SET quantity = ?, last_updated = datetime('now') WHERE id = ?",
                                   (new_quantity, stock_entry[0]))
                else: # Insert new stock entry
                    cursor.execute("INSERT INTO CenterStock (center_id, vaccine_id, quantity, last_updated) VALUES (?, ?, ?, datetime('now'))",
                                   (self.managed_center_id, vaccine_id, quantity_change))
                action_text = "added"
            elif operation == "remove":
                if not stock_entry or stock_entry[1] < quantity_change:
                    messagebox.showerror("Stock Error", f"Not enough stock of {vaccine_name} to remove. Available: {stock_entry[1] if stock_entry else 0}", parent=self.root)
                    conn.rollback()
                    return
                new_quantity = stock_entry[1] - quantity_change
                cursor.execute("UPDATE CenterStock SET quantity = ?, last_updated = datetime('now') WHERE id = ?",
                               (new_quantity, stock_entry[0]))
                action_text = "removed"
            else: # Should not happen
                conn.rollback()
                return

            conn.commit()
            messagebox.showinfo("Success", f"{quantity_change} dose(s) of {vaccine_name} {action_text} successfully for {self.managed_center_name}.", parent=self.root)
            self.update_current_stock_display()
            self.load_center_stock_overview() # Refresh the full list
            self.status_label.config(text=f"Stock for {vaccine_name} updated.")

        except sqlite3.Error as e:
            if conn: conn.rollback()
            messagebox.showerror("Database Error", f"Failed to {operation} stock: {e}", parent=self.root)
        finally:
            if conn:
                conn.close()

    def add_stock(self):
        self._modify_stock(operation="add")

    def remove_stock(self):
        self._modify_stock(operation="remove")

    def load_center_stock_overview(self):
        """Loads and displays all vaccine stock for the managed center."""
        self.center_stock_listbox.delete(0, END)
        if not self.managed_center_id:
            self.center_stock_listbox.insert(END, "No center assigned to view stock.")
            return

        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.Med_name, cs.quantity, cs.last_updated
                FROM CenterStock cs
                JOIN Medicine m ON cs.vaccine_id = m.id
                WHERE cs.center_id = ?
                ORDER BY m.Med_name
            """, (self.managed_center_id,))
            
            all_stock = cursor.fetchall()
            if all_stock:
                for med_name, qty, updated_at in all_stock:
                    self.center_stock_listbox.insert(END, f"{med_name}: {qty} doses (Updated: {updated_at or 'N/A'})")
            else:
                self.center_stock_listbox.insert(END, f"No stock records found for {self.managed_center_name}.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to load stock overview: {e}", parent=self.root)
            self.center_stock_listbox.insert(END, "Error loading stock overview.")
        finally:
            if conn:
                conn.close()


# This is for standalone testing
if __name__ == "__main__":
    # Ensure the database exists. Run database.py first.
    # For testing, use a center admin's person_id.
    # Let's assume person_id 6 is 'admin1@example.com' (Claire Admin)
    mock_admin_person_id = 6 
    mock_admin_role = "center_admin"

    if not os.path.exists(DB_PATH):
        print(f"Database file '{DB_PATH}' not found. Please run database.py first.")
    else:
        conn_test = None
        try:
            conn_test = sqlite3.connect(DB_PATH)
            cursor_test = conn_test.cursor()
            # Verify if the mock admin exists
            cursor_test.execute("SELECT person_id FROM Credentials WHERE person_id = ? AND user_type = 'center_admin'", (mock_admin_person_id,))
            if cursor_test.fetchone():
                app = CenterAdminMainPage(current_user_id=mock_admin_person_id, current_user_role=mock_admin_role)
                app.run()
            else:
                print(f"Test admin with person_id {mock_admin_person_id} not found or is not a center_admin.")
        except sqlite3.Error as e:
            print(f"Database error during test setup: {e}")
        finally:
            if conn_test:
                conn_test.close()