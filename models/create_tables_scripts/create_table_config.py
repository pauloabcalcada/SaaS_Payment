from sqlalchemy import create_engine, Column, Integer, String,Text
from sqlalchemy.ext.declarative import declarative_base
from database import engine


# Create a base class for declarative models
Base = declarative_base()

# Define the Configuracoes model
class Configuracoes(Base):
    __tablename__ = 'Configuracoes'

    Id_Parametro = Column(Integer, primary_key=True, autoincrement=True)
    Nome_Parametro = Column(String(255), nullable=False)  # Parameter name
    Valor_Atual = Column(Text, nullable=False)  # Current value

# Drop and recreate the table
if __name__ == "__main__":
    # Drop the table if it exists
    Base.metadata.drop_all(engine)
    print("Existing table 'Configuracoes' dropped successfully!")

    # Create the table with the updated schema
    Base.metadata.create_all(engine)
    print("Table 'Configuracoes' created successfully!")