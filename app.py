# The API
from flask import Flask, jsonify, send_from_directory, request
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
 
app = Flask(__name__, static_folder='public', static_url_path='')

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        ssl_disabled=True
    )

@app.route('/')
def serve_index():
    return send_from_directory('public', 'index.html')

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True) # Return as JSON objects instead of tuples
    query = """
        SELECT summary_code, description 
        FROM icd_summary_codes 
        ORDER BY summary_code;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

# Summarizes all admissions data up to the 22-chapter level (default)
@app.route('/api/admissions/summary', methods=['GET'])
def get_summary_admissions():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            s.summary_code,
            s.description AS chapter_name,
            a.financial_year,
            SUM(a.total_admissions) AS total,
            SUM(a.emergency_admissions) AS emergency,
            SUM(a.planned_admissions) AS planned
        FROM yearly_admissions a
        JOIN icd_3char_codes c ON a.code = c.code
        JOIN icd_summary_codes s ON c.summary_code = s.summary_code
        GROUP BY s.summary_code, s.description, a.financial_year
        ORDER BY s.summary_code, a.financial_year;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

@app.route('/api/admissions/chapter/<summary_code>', methods=['GET'])
def get_chapter_details(summary_code):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            c.code AS diagnosis_code,
            c.description AS diagnosis_name,
            a.financial_year,
            SUM(a.total_admissions) AS total,
            SUM(a.emergency_admissions) AS emergency,
            SUM(a.planned_admissions) AS planned
        FROM yearly_admissions a
        JOIN icd_3char_codes c ON a.code = c.code
        WHERE c.summary_code = %s
        GROUP BY c.code, c.description, a.financial_year
        ORDER BY c.code, a.financial_year;
    """
    cursor.execute(query, (summary_code,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

# Returns a master list of all 3-char codes for the Custom View search bar
@app.route('/api/codes', methods=['GET'])
def get_all_codes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT code, description FROM icd_3char_codes ORDER BY code;")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

# Accepts a JSON array of specific codes and returns their admissions data
@app.route('/api/admissions/custom', methods=['POST'])
def get_custom_admissions():
    requested_codes = request.json.get('codes', [])
    if not requested_codes:
        return jsonify([])
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(requested_codes))
    query = f"""
        SELECT 
            c.code AS diagnosis_code,
            c.description AS diagnosis_name,
            a.financial_year,
            SUM(a.total_admissions) AS total,
            SUM(a.emergency_admissions) AS emergency,
            SUM(a.planned_admissions) AS planned
        FROM yearly_admissions a
        JOIN icd_3char_codes c ON a.code = c.code
        WHERE c.code IN ({format_strings})
        GROUP BY c.code, c.description, a.financial_year
        ORDER BY c.code, a.financial_year;
    """
    cursor.execute(query, tuple(requested_codes))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
