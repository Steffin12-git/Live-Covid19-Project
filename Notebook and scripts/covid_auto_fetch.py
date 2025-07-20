import requests
import pandas as pd
import sqlite3
from datetime import datetime

# -------- CONFIGURATION -------- #
API_URL = "https://disease.sh/v3/covid-19/countries"

DB_PATH = r"D:\Data\Projects\Covid data\Live-Covid19-Project\Live covid19 dataset\covid_data.db"
LOG_FILE = r"D:\Data\Projects\Covid data\Live-Covid19-Project\Log files\log.txt"
ERROR_LOG = r"D:\Data\Projects\Covid data\Live-Covid19-Project\Log files\error_log.txt"
EXCEL_PATH = r"D:\Data\Projects\Covid data\Live-Covid19-Project\Live covid19 dataset\covid_data_exported.xlsx"

# -------- FETCH DATA FROM API -------- #
try:
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: ❌ Error fetching data - {str(e)}\n")
    exit()

# -------- PROCESS DATA -------- #
df = pd.json_normalize(data)
df['fetch_date'] = datetime.now().strftime('%Y-%m-%d')

# Keep only required columns
required_columns = [
    'country', 'cases', 'todayCases', 'deaths', 'todayDeaths',
    'recovered', 'todayRecovered', 'active', 'critical', 'population', 'fetch_date'
]
df = df[required_columns]

# -------- DATABASE OPERATIONS -------- #
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_data (
            country TEXT,
            cases INTEGER,
            todayCases INTEGER,
            deaths INTEGER,
            todayDeaths INTEGER,
            recovered INTEGER,
            todayRecovered INTEGER,
            active INTEGER,
            critical INTEGER,
            population INTEGER,
            fetch_date TEXT
        )
    ''')

    # Check if today's data already exists (ensure all or most countries are present)
    fetch_date = df['fetch_date'].iloc[0]
    cursor.execute("SELECT COUNT(DISTINCT country) FROM daily_data WHERE fetch_date = ?", (fetch_date,))
    existing_count = cursor.fetchone()[0]

    if existing_count >= 180:
        print("✅ Data for today already exists. Skipping insertion.")
    else:
        df.to_sql('daily_data', conn, if_exists='append', index=False)
        print("✅ New data inserted.")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}: ✅ New data inserted successfully.\n")

    # -------- EXPORT FULL TABLE TO EXCEL -------- #
    df = pd.read_sql_query("SELECT * FROM daily_data", conn)
    df.to_excel(EXCEL_PATH, index=False, sheet_name='Covid_data')
    print(f"📁 Excel file updated: {EXCEL_PATH}")

except Exception as db_err:
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: ❌ Database error - {str(db_err)}\n")
finally:
    conn.close()

print("Script completed ✅")
