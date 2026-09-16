import os
import duckdb

# Create an export directory if it doesn't already exist
export_dir = "data/gold_layer"
os.makedirs(export_dir, exist_ok=True)

# Connect to your database
con = duckdb.connect('data_modeling/dev.duckdb') 

# Target only dim_ and fact_ tables (the gold layer)
gold_tables = con.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE 'dim_%' OR table_name LIKE 'fact_%'
""").fetchall()

print(f"Found {len(gold_tables)} gold tables to export:")

for (table_name,) in gold_tables:
    file_path = os.path.join(export_dir, f"{table_name}.csv")
    print(f"Exporting -> {file_path}")
    con.execute(f"COPY {table_name} TO '{file_path}' (HEADER, DELIMITER ',')")

print("Export complete!")
