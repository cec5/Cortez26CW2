# NHS Hospital Admissions Visualizer: Lockdown Impact

## Overview
This project is a simple locally hosted web application designed to visually analyze the impact of the 2020-2021 COVID-19 lockdown on NHS hospital admissions in England. By utilizing a custom-built interactive Matrix Chart (Heatmap), it allows users to longitudinally compare admission trends across 22 ICD-10 chapters and specific 3-character diagnoses. 

It was created for the University of Notttingham's Research Method's (COMP4037) Module as part of Coursework II.

## Features
* **Interactive Heatmap:** View longitudinal data (2016-2023).
* **Macro View & Chapter Drill-down:** Start with a high-level view of all 22 ICD-10 Chapters, then drill down into specific chapters.
* **Custom Builder:** A search-driven interface to dynamically compare specific diagnoses.
* **Dynamic Metric Toggles:** Switch seamlessly between Total, Emergency, and Planned admissions.

---

## Getting Started (Ubuntu Environment)

### 1. Prerequisites
Ensure your local Ubuntu machine is fully updated and has the core system packages installed:

```bash
sudo apt update
sudo apt install mysql-server python3 python3-flask python3-mysql.connector python3-pandas python3-dotenv python3-openpyxl -y
```

### 2. Clone the Repository
You must download or clone the repository, you may do so by running the following command:
```bash
git clone https://github.com/cec5/Cortez26CW2.git
```

### 3. Database Setup
The application relies on a MySQL database. You need to create the database, set up the specific admin user, and import the provided SQL dump.

Access the MySQL prompt as the root user:
```bash
sudo mysql
```

Execute the following SQL commands to create the database and the `admin` user.
```sql
CREATE DATABASE NHSData;
CREATE USER 'admin'@'localhost' IDENTIFIED WITH mysql_native_password BY 'admin';
GRANT ALL PRIVILEGES ON NHSData.* TO 'admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Restore the database from the provided SQL dump file. From the root directory of this project, run:
```bash
mysql -u admin -p NHSData < src/database/database.backup.sql
```
*(When prompted for a password, type: `admin`)*

### 4. Environment Variables
In the root directory of the project (where `app.py` is located), create a `.env` file to hold the credentials.

```bash
touch .env
nano .env
```

Add the following lines to the `.env` file, save, and exit:
```env
DB_HOST=localhost
DB_USER=admin
DB_PASS=admin
DB_NAME=NHSData
```

### 5. Running the Application
Ensure you are in the project root directory (where `app.py` is located).

Start the Flask backend server:
```bash
python3 app.py
```

Open your web browser and navigate to:
**http://localhost:5000**
