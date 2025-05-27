import sqlite3

# Connect to SQLite
conn = sqlite3.connect("local_database.db")

# List of tables to drop
tables_to_drop = ["Clientes", "Configuracoes", "Pagamentos"]

# Drop each table
for table in tables_to_drop:
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"Table {table} dropped successfully.")
    except Exception as e:
        print(f"Error dropping table {table}: {e}")

# Close the connection
conn.close()