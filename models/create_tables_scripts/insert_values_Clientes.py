import random
from sqlalchemy.orm import sessionmaker
from src.models.database import engine
from src.models.tables import Cliente

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Function to generate random values and insert into Cliente table
def insert_random_clientes(num_records=10):
    try:
        for i in range(num_records):
            cliente = Cliente(
                Nome_da_Empresa=f"Empresa {i + 1}",
                CNPJ=f"{random.randint(10000000000000, 99999999999999)}",  # Random 14-digit CNPJ
                Telefone=f"({random.randint(10, 99)}) {random.randint(90000, 99999)}-{random.randint(1000, 9999)}",  # Random phone number
                Email="pauloazevedo@poli.ufrj.br",  # Constant email
                Endereco=f"Rua {random.randint(1, 1000)}, Bairro {random.randint(1, 50)}",
                Dia_do_Vencimento=random.randint(1, 28),  # Random day of the month
                Valor_da_Conta=round(random.uniform(100.0, 10000.0), 2)  # Random value between 100.0 and 10000.0
            )
            session.add(cliente)

        # Commit the transaction
        session.commit()
        print(f"{num_records} registros inseridos com sucesso na tabela Cliente!")
    except Exception as e:
        session.rollback()
        print(f"Erro ao inserir registros: {e}")
    finally:
        session.close()

# Run the function
if __name__ == "__main__":
    insert_random_clientes(num_records=10)  # Insert 10 random records