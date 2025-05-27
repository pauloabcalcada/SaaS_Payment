from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from models.database import engine


# Create a base class for declarative models
Base = declarative_base()

# Define the Cliente model
class Cliente(Base):
    __tablename__ = 'Clientes'

    Id_empresa = Column(Integer, primary_key=True, autoincrement=True)
    Nome_da_Empresa = Column(String(255), nullable=False)  # New column added
    CNPJ = Column(String(20), nullable=False)
    Telefone = Column(String(20), nullable=False)
    Email = Column(String(255), nullable=False)
    Endereco = Column(String(255), nullable=False)
    Dia_do_Vencimento = Column(Integer, nullable=False)
    Valor_da_Conta = Column(Float, nullable=False)

# Drop and recreate the table
if __name__ == "__main__":
    # Drop the table if it exists
    Base.metadata.drop_all(engine)
    print("Existing table 'Clientes' dropped successfully!")

    # Create the table with the updated schema
    Base.metadata.create_all(engine)
    print("Table 'Clientes' created successfully!")