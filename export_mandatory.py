import psycopg2
import openpyxl
from datetime import datetime

conn = psycopg2.connect(
    dbname="ztb_db", user="ztb_user", password="ztb_pass_2026!xK9", host="localhost", port="5432"
)
cur = conn.cursor()

# Find all tables with a mandatory column
cur.execute("""
    SELECT table_name FROM information_schema.columns 
    WHERE column_name = 'mandatory' AND table_schema = 'public'
""")
tables = [row[0] for row in cur.fetchall()]

wb = openpyxl.Workbook()
wb.remove(wb.active)  # remove default sheet

for table in tables:
    cur.execute(f"SELECT * FROM {table} WHERE mandatory = true")
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]

    ws = wb.create_sheet(title=table[:31])  # sheet name max 31 chars
    ws.append(cols)
    for row in rows:
        ws.append([str(v) if v is not None else '' for v in row])

filename = f"/home/ubuntu/ztb-super-app/mandatory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
wb.save(filename)
print(f"Exported to: {filename}")

cur.close()
conn.close()
