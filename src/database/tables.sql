CREATE TABLE IF NOT EXISTS icd_summary_codes (
    summary_code VARCHAR(15) PRIMARY KEY,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS icd_3char_codes (
    code VARCHAR(3) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    summary_code VARCHAR(15),
    FOREIGN KEY (summary_code) REFERENCES icd_summary_codes(summary_code)
);

CREATE TABLE IF NOT EXISTS yearly_admissions (
    financial_year VARCHAR(7),
    code VARCHAR(3),
    total_admissions INT,
    emergency_admissions INT,
    planned_admissions INT,
    PRIMARY KEY (financial_year, code), 
    FOREIGN KEY (code) REFERENCES icd_3char_codes(code)
);
