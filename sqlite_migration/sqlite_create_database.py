import sqlite3

# Connect to SQLite (creates the database file if it doesn't exist)
conn = sqlite3.connect("local_database.db")

# Define the schema for the Clientes table
clientes_schema = """
CREATE TABLE IF NOT EXISTS Clientes (
    Id_empresa INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome_da_Empresa TEXT NOT NULL,
    CNPJ TEXT NOT NULL,
    Telefone TEXT NOT NULL,
    Email TEXT NOT NULL,
    Endereco TEXT NOT NULL,
    Dia_do_Vencimento INTEGER NOT NULL,
    Valor_da_Conta REAL NOT NULL
);
"""

# Define the schema for the Configuracoes table
configuracoes_schema = """
CREATE TABLE IF NOT EXISTS Configuracoes (
    Id_Parametro INTEGER PRIMARY KEY AUTOINCREMENT,
    Nome_Parametro TEXT NOT NULL,
    Valor_Atual TEXT NOT NULL
);
"""

# Define the schema for the Pagamentos table
pagamentos_schema = """
CREATE TABLE IF NOT EXISTS Pagamentos (
    Id_pagamento INTEGER PRIMARY KEY AUTOINCREMENT,
    Id_empresa INTEGER NOT NULL,
    Nome_da_Empresa TEXT NOT NULL,
    Prazo_Vencimento DATE NOT NULL,
    Email TEXT NOT NULL,
    Valor_da_Conta REAL NOT NULL,
    Status_Pagamento TEXT NOT NULL,
    Status_Dias_Vencimento TEXT,
    Data_do_Pagamento DATE,
    Dias_Pagamento_Vencimento INTEGER,
    FOREIGN KEY (Id_empresa) REFERENCES Clientes (Id_empresa) ON DELETE CASCADE
);
"""

# Execute the schema creation
conn.execute(clientes_schema)
print("Created Clientes table in SQLite database.")

conn.execute(configuracoes_schema)
print("Created Configuracoes table in SQLite database.")

conn.execute(pagamentos_schema)
print("Created Pagamentos table in SQLite database.")

conn.close()