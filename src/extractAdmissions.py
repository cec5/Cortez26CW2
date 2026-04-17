# Script that extracts admissions data from the given files and inserts them into the database
import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def ingest_yearly_admissions(file_path, sheet_name, header_row_index, financial_year, col_indices):
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_row_index)

    df['code'] = df.iloc[:, 0].astype(str).str.strip().str[:3]
    df = df[df['code'].str.match(r'^[A-Z][0-9]{2}$')]
    
    adm_idx = col_indices.get('admissions')
    emg_idx = col_indices.get('emergency')
    pln_idx = col_indices.get('planned')
    
    df['total_admissions'] = pd.to_numeric(df.iloc[:, adm_idx], errors='coerce').fillna(0).astype(int)
    df['emergency_admissions'] = pd.to_numeric(df.iloc[:, emg_idx], errors='coerce').fillna(0).astype(int)
    df['planned_admissions'] = pd.to_numeric(df.iloc[:, pln_idx], errors='coerce').fillna(0).astype(int)
    df['financial_year'] = financial_year
    
    insert_df = df[['financial_year', 'code', 'total_admissions', 'emergency_admissions', 'planned_admissions']]
    records_to_insert = list(insert_df.itertuples(index=False, name=None))

    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            ssl_disabled=True
        )
        cursor = conn.cursor()
        insert_query = """
            INSERT IGNORE INTO yearly_admissions 
            (financial_year, code, total_admissions, emergency_admissions, planned_admissions)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"SUCCESS: Inserted {cursor.rowcount} records for the {financial_year} financial year.")
        
    except mysql.connector.Error as err:
        print(f"ERROR: Database Error during Admissions ingestion for {financial_year}: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    data_directory = 'data'
    sheet_name = 'Primary Diagnosis 3 Character'

    # Should have done this for extractCodes, oh well...
    processing_queue = [
        {
            'file': 'hosp-epis-stat-admi-diag-2016-17-tab.xlsx',
            'year': '2016-17',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2017-18-tab.xlsx',
            'year': '2017-18',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2018-19-tab.xlsx',
            'year': '2018-19',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2019-20-tab.xlsx',
            'year': '2019-20',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2020-21-tab.xlsx',
            'year': '2020-21',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2021-22-tab.xlsx',
            'year': '2021-22',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        },
        {
            'file': 'hosp-epis-stat-admi-diag-2022-23-tab.xlsx',
            'year': '2022-23',
            'skiprows': 12,
            'indices': {'admissions': 8, 'emergency': 12, 'planned': 14}
        }
    ]

    print("Starting ingestion of yearly admission data")
    for item in processing_queue:
        file_path = os.path.join(data_directory, item['file'])
        if os.path.exists(file_path):
            print(f"Processing {item['year']}...")
            ingest_yearly_admissions(file_path=file_path, sheet_name=sheet_name, header_row_index=item['skiprows'], financial_year=item['year'], col_indices=item['indices'])
        else:
            print(f"ERROR: File not found: {file_path}")