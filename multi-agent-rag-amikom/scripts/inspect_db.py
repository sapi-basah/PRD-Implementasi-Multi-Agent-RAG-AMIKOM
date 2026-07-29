import sqlite3
import json

db_path = "./data/immutable/vector_db/Vector_Database_RAG_AMIKOM_V1/01_database/metadata.sqlite"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Columns
cursor.execute("PRAGMA table_info(vector_records)")
cols = cursor.fetchall()
print("\nColumns:")
for c in cols:
    print(f"  {c}")

# Total records
cursor.execute("SELECT COUNT(*) FROM vector_records")
print(f"\nTotal records: {cursor.fetchone()[0]}")

# Namespaces
cursor.execute("SELECT DISTINCT retrieval_namespace FROM vector_records")
print("Namespaces:", [r[0] for r in cursor.fetchall()])

# Lifecycle statuses
cursor.execute("SELECT DISTINCT lifecycle_status FROM vector_records")
print("Lifecycle:", [r[0] for r in cursor.fetchall()])

# NS counts
cursor.execute("SELECT retrieval_namespace, COUNT(*) FROM vector_records GROUP BY retrieval_namespace")
print("NS counts:", cursor.fetchall())

# Historical only
cursor.execute("SELECT DISTINCT historical_only FROM vector_records")
print("Historical_only values:", [r[0] for r in cursor.fetchall()])

# Sample record
cursor.execute("SELECT * FROM vector_records LIMIT 1")
row = cursor.fetchone()
col_names = [d[0] for d in cursor.description]
print("\nSample record fields:", col_names)

conn.close()
