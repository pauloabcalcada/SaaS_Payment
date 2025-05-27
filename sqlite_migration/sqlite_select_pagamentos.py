import sqlite3

# Connect to SQLite
conn = sqlite3.connect("local_database.db")

# Query the Pagamentos table
query = "SELECT * FROM Configuracoes;"
cursor = conn.execute(query)

# Print the results
columns = [description[0] for description in cursor.description]
rows = cursor.fetchall()

print("Pagamentos Table (First 10 Rows):")
print(columns)
for row in rows:
    print(row)

conn.close()