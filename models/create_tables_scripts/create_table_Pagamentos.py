from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from  src.models.database import engine
from src.models.tables import Cliente


# Create a base class for declarative models
Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'Clientes'

    Id_empresa = Column(Integer, primary_key=True, autoincrement=True)
    Nome_da_Empresa = Column(String(255), nullable=False)
    CNPJ = Column(String, nullable=False)
    Telefone = Column(String, nullable=False)
    Email = Column(String, nullable=False)
    Endereco = Column(String, nullable=False)
    Dia_do_Vencimento = Column(Integer, nullable=False)
    Valor_da_Conta = Column(Float, nullable=False)
    
# Define the Pagamentos model
class Pagamentos(Base):
    __tablename__ = 'Pagamentos'

    Id_pagamento = Column(Integer, primary_key=True, autoincrement=True)
    Id_empresa = Column(Integer, ForeignKey('Clientes.Id_empresa'), nullable=False)  # Foreign key to Clientes
    Nome_da_Empresa = Column(String(255), nullable=False)
    Prazo_Vencimento = Column(Date, nullable=False)
    Email = Column(String(255), nullable=False)
    Valor_da_Conta = Column(Float, nullable=False)
    Status_Pagamento = Column(String(50), nullable=False)
    Status_Dias_Vencimento = Column(String(255), nullable=True)
    Data_do_Pagamento = Column(Date, nullable=True)
    Dias_Pagamento_Vencimento = Column(Integer, nullable=True)



# Drop and recreate the table
if __name__ == "__main__":
    # Drop the table if it exists
    Base.metadata.drop_all(engine)
    print("Existing table 'Pagamentos' dropped successfully!")

    # Create the table with the updated schema
    Base.metadata.create_all(engine)
    print("Table 'Pagamentos' created successfully!")