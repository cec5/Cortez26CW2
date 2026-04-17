# Simple Script to extract and insert codes
import pandas as pd
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

ICD10_CHAPTERS = {
    'A00-B99': 'Certain infectious and parasitic diseases',
    'C00-D48': 'Neoplasms',
    'D50-D89': 'Diseases of the blood and blood-forming organs and certain disorders involving the immune mechanism',
    'E00-E90': 'Endocrine, nutritional and metabolic diseases',
    'F00-F99': 'Mental and behavioural disorders',
    'G00-G99': 'Diseases of the nervous system',
    'H00-H59': 'Diseases of the eye and adnexa',
    'H60-H95': 'Diseases of the ear and mastoid process',
    'I00-I99': 'Diseases of the circulatory system',
    'J00-J99': 'Diseases of the respiratory system',
    'K00-K93': 'Diseases of the digestive system',
    'L00-L99': 'Diseases of the skin and subcutaneous tissue',
    'M00-M99': 'Diseases of the musculoskeletal system and connective tissue',
    'N00-N99': 'Diseases of the genitourinary system',
    'O00-O99': 'Pregnancy, childbirth and the puerperium',
    'P00-P96': 'Certain conditions originating in the perinatal period',
    'Q00-Q99': 'Congenital malformations, deformations and chromosomal abnormalities',
    'R00-R99': 'Symptoms, signs and abnormal clinical and laboratory findings, not elsewhere classified',
    'S00-T98': 'Injury, poisoning and certain other consequences of external causes',
    'V01-Y98': 'External causes of morbidity and mortality',
    'Z00-Z99': 'Factors influencing health status and contact with health services',
    'U00-U99': 'Codes for special purposes'
}

def expand_summary_range(range_string):
    range_string = str(range_string).strip().upper()
    
    if '-' not in range_string:
        return [range_string] if range_string else []
        
    try:
        start_code, end_code = range_string.split('-')
        start_letter, start_num = start_code[0], int(start_code[1:])
        end_letter, end_num = end_code[0], int(end_code[1:])
        
        expanded_codes = []

        for ascii_val in range(ord(start_letter), ord(end_letter) + 1):
            current_letter = chr(ascii_val)
            current_start = start_num if current_letter == start_letter else 0
            current_end = end_num if current_letter == end_letter else 99
            for i in range(current_start, current_end + 1):
                expanded_codes.append(f"{current_letter}{i:02d}")
        return expanded_codes
    except ValueError:
        return []

def insert_ICD10_chapters():
    records_to_insert = list(ICD10_CHAPTERS.items())
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database=os.getenv("DB_NAME"),
            ssl_disabled=True
        )
        cursor = conn.cursor()
        # Not like I'm going to perform an insertion attack against myself but...
        insert_query = """
            INSERT IGNORE INTO icd_summary_codes (summary_code, description)
            VALUES (%s, %s)
        """
        cursor.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"SUCCESS: Inserted {cursor.rowcount} ICD10 Chapters in the database.")
    except mysql.connector.Error as err: # Shouldn't actually happen but...
        print(f"ERROR: Database Error during ICD10 Chapter processing: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# Used for mapping 3-char codes from the sheet to the appropriate ICD10 Chapter
def build_chapter_mapping():
    code_to_summary_map = {}
    for summary_code in ICD10_CHAPTERS.keys():
        expanded_codes = expand_summary_range(summary_code)
        for code in expanded_codes:
            code_to_summary_map[code] = summary_code
    return code_to_summary_map

# Extracts and inserts the 3-character codes from the provided sheet
def ingest_3char_codes(file_path, sheet_name, header_rows, mapping_dict):
    df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_rows)
    
    codes_df = df.iloc[:, [0, 1]].dropna()
    codes_df.columns = ['code', 'description']
    codes_df['code'] = codes_df['code'].astype(str).str.strip().str[:3]
    codes_df['description'] = codes_df['description'].astype(str).str.strip()
    codes_df = codes_df[codes_df['code'].str.match(r'^[A-Z][0-9]{2}$')]
    codes_df['summary_code'] = codes_df['code'].map(lambda x: mapping_dict.get(x, None))

    records_to_insert = list(codes_df.itertuples(index=False, name=None))

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
            INSERT IGNORE INTO icd_3char_codes (code, description, summary_code)
            VALUES (%s, %s, %s)
        """
        cursor.executemany(insert_query, records_to_insert)
        conn.commit()
        print(f"SUCCESS: Processed {cursor.rowcount} new 3-character codes from {file_path}")
        
    except mysql.connector.Error as err:
        print(f"ERROR: Database Error during 3-Character ingestion: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# Adjust as needed
if __name__ == "__main__":
    data_directory = 'data'
    sheet_name = 'Primary Diagnosis 3 Character'
    file_name = 'hosp-epis-stat-admi-diag-2022-23-tab.xlsx'
    file_to_process = os.path.join(data_directory, file_name)
    if os.path.exists(file_to_process):
        print("Starting normalization and ingestion")
        insert_ICD10_chapters()
        mapping_dictionary = build_chapter_mapping()
        if mapping_dictionary:
            ingest_3char_codes(file_to_process, sheet_name, 12, mapping_dictionary)
        else:
            print("ERROR: Failed to process or link 3-character codes.")
    else:
        print(f"ERROR: File not found: {file_to_process}")