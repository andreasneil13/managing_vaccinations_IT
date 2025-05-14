# managing_vaccinations_IT
# Vaccination Management System

## Overview

This project is a desktop application for managing vaccinations, developed as a proof-of-concept for a medical information system. It simulates a platform where different healthcare stakeholders (doctors, patients, nurses, and vaccination center administrators) can interact with a centralized vaccination database. The application is built using Python with Tkinter for the graphical user interface and SQLite for the database.

## Features

The system provides tailored functionalities for four distinct user roles:

### 1. Doctor
* **Login & Registration:** Doctors can create an account and log in to the system.
* **Patient Registration:** Doctors are responsible for registering new patients into the system.
* **View Vaccine List:** Can view a list of all available vaccines in the system (not specific stock levels).
* **Access Patient Files:** Can search for and view the medical records of their assigned patients, including vaccination history and pending prescriptions.
* **Prescribe Vaccines:** Can prescribe specific vaccines to their patients, creating a new prescription record.

### 2. Patient
* **Login Only:** Patients can log in using credentials created for them by a doctor.
* **View Vaccination History:** Can view their complete record of administered vaccines.
* **View New Prescriptions:** Can see any new vaccines that have been prescribed to them by their doctor and are pending administration.
* **Check Vaccine Availability:** Can check at which vaccination centers their prescribed (and pending) vaccines are currently in stock.

### 3. Nurse
* **Login & Registration:** Nurses can create an account and log in.
* **Access Patient Files:** Can search for any patient and view their medical records, including prescriptions and vaccination history.
* **View New Prescriptions:** Can see pending vaccine prescriptions for a selected patient.
* **Administer Vaccines:** Can record the administration of a vaccine to a patient. This action updates the prescription status to 'administered' and (conceptually) removes the vaccine dose from the stock of the administering center.

### 4. Center Administrator
* **Login & Registration:** Center administrators can create an account and log in.
* **Register/Assign Center:** Can register a new vaccination center or take administrative control of an existing, unmanaged center. Each admin manages one center.
* **Manage Vaccine Stock:** Can add or remove quantities of specific vaccines from their assigned center's inventory.
* **View Center Stock:** Can view the current stock levels for all vaccines at their center.
* **No Patient Data Access:** Center administrators cannot access any patient-specific medical data.

## Technologies Used

* **Programming Language:** Python 3
* **GUI:** Tkinter (standard Python interface to the Tk GUI toolkit)
* **Database:** SQLite 3
* **Styling:** `ttk` themed widgets for a more modern look.

## Setup and Installation

1.  **Prerequisites:**
    * Python 3.x installed on your system.
    * SQLite 3 (usually comes bundled with Python).

2.  **Clone the Repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory-name>
    ```

3.  **No External Libraries to Install:**
    This project uses Python's built-in libraries (tkinter, sqlite3, os, re). No `pip install` is required for external packages.

## Database

The application uses an SQLite database named `vaccinedatabase.db`.

* **Initialization:** The database schema and initial sample data are created by running the `database.py` script. This script should be run once before starting the application for the first time.
    ```bash
    python database.py
    ```
    This will create the `vaccinedatabase.db` file in the same directory.
* **Schema:** The database schema includes tables for `Person`, `Credentials`, `Doctor`, `Nurse`, `CenterAdmin`, `Patient`, `DoctorPatient` (junction table), `Medicine` (vaccines), `Prescription`, `VaccinationCenter`, `CenterStock`, and `AdministrationLog`. Refer to the `database.py` script or the `vaccination_database.sql` file for detailed schema information.

## How to Run the Application

1.  **Ensure the database is initialized:** If you haven't already, run `python database.py`.
2.  **Start the Login Portal:** Execute the `login.py` script.
    ```bash
    python login.py
    ```
    This will open the main login window, from where users can log in or register (for staff roles).

## Project Structure

The project is organized into the following Python files:

* `database.py`: Initializes the SQLite database, creates tables, and populates with sample data.
* `login.py`: Main entry point of the application; handles user login and registration for staff.
* `main_page.py`: A base class providing common UI elements and functionalities for the different user dashboards.
* `doctor_main_page.py`: Implements the dashboard and features for the Doctor role.
* `patient_main_page.py`: Implements the dashboard and features for the Patient role.
* `nurse_main_page.py`: Implements the dashboard and features for the Nurse role.
* `center_admin_main_page.py`: Implements the dashboard and features for the Center Administrator role.
* `vaccination_database.sql`: An SQL script containing the schema and sample data, which can be used to set up the database with an SQL client.

## Future Improvements (Examples)

* More robust error handling and input validation.
* Enhanced UI/UX design.
* Password hashing for security.
* Direct linking of nurses to specific vaccination centers.
* More detailed reporting features.
* Integration with external medical coding systems (e.g., for vaccine types).
