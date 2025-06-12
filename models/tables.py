from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'Clientes'

    Id_empresa = Column(Integer, primary_key=True, autoincrement=True)
    Nome_da_Empresa = Column(String(255), nullable=False)
    CNPJ = Column(String(32), nullable=False)
    Telefone = Column(String(32), nullable=False)
    Email = Column(String(255), nullable=False)
    Endereco = Column(String(255), nullable=False)
    Dia_do_Vencimento = Column(Integer, nullable=False)
    Valor_da_Conta = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Cliente(Id_empresa={self.Id_empresa}, CNPJ='{self.CNPJ}', Telefone='{self.Telefone}', Email='{self.Email}', Endereco='{self.Endereco}', Dia_do_Vencimento={self.Dia_do_Vencimento}, Valor_da_Conta={self.Valor_da_Conta})>"

    @classmethod
    def create(cls, session, **kwargs):
        new_cliente = cls(**kwargs)
        session.add(new_cliente)
        session.commit()
        return new_cliente

    @classmethod
    def read(cls, session, id_empresa):
        return session.query(cls).filter_by(Id_empresa=id_empresa).first()

    @classmethod
    def update(cls, session, id_empresa, **kwargs):
        cliente = session.query(cls).filter_by(Id_empresa=id_empresa).first()
        for key, value in kwargs.items():
            setattr(cliente, key, value)
        session.commit()
        return cliente

    @classmethod
    def delete(cls, session, id_empresa):
        cliente = session.query(cls).filter_by(Id_empresa=id_empresa).first()
        session.delete(cliente)
        session.commit()
        return cliente

class Configuracoes(Base):
    __tablename__ = 'Configuracoes'

    Id_Parametro = Column(Integer, primary_key=True, autoincrement=True)
    Nome_Parametro = Column(String(255), nullable=False)
    Valor_Atual = Column(Text, nullable=False)

class Pagamentos(Base):
    __tablename__ = 'Pagamentos'

    Id_pagamento = Column(Integer, primary_key=True, autoincrement=True)
    Id_empresa = Column(Integer, ForeignKey('Clientes.Id_empresa', ondelete="CASCADE"), nullable=False)
    Nome_da_Empresa = Column(String(255), nullable=False)
    Prazo_Vencimento = Column(Date, nullable=False)
    Email = Column(String(255), nullable=False)
    Valor_da_Conta = Column(Float, nullable=False)
    Status_Pagamento = Column(String(50), nullable=False)
    Status_Dias_Vencimento = Column(String(255), nullable=True)
    Data_do_Pagamento = Column(Date, nullable=True)
    Dias_Pagamento_Vencimento = Column(Integer, nullable=True)
    Tipo_Pagamento = Column(String(32), nullable=True)  # New column for PostgreSQL
