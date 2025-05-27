import sqlite3
import pandas as pd

# Connect to SQLite
conn = sqlite3.connect("local_database.db")

# List of CSV files to import
csv_files = ["Clientes.csv","Configuracoes.csv","Pagamentos.csv"]  # Add more CSV file names as needed

# Import each CSV file into the corresponding SQLite table
for csv_file in csv_files:
    table_name = csv_file.split(".")[0]  # Extract table name from file name
    df = pd.read_csv(csv_file)
    df.to_sql(table_name, conn, if_exists="append", index=False)
    print(f"Imported {csv_file} into {table_name} table.")

conn.close()