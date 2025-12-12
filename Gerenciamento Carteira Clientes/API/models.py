from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from db import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    pais = Column(String)
    estado = Column(String)
    regiao = Column(String)
    municipio = Column(String)
    bairro = Column(String)
    rua = Column(String)
    numero = Column(String)
    cnpj = Column(String)
    contato = Column(String)
    email = Column(String)
    maquinas = Column(Text)
    producao = Column(Text)
    quantidade = Column(Integer)
    status = Column(String)
    ultima_compra = Column(Date)
    lembrete_dias = Column(Integer)
    lat = Column(Float)  
    lon = Column(Float)  
    nome_fantasia = Column(String)
    # Relacionamento com peças
    pecas = relationship("PecasClientes", back_populates="cliente")

class PecasClientes(Base):
    __tablename__ = "pecas_clientes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    maquina = Column(String, nullable=False)
    peca = Column(String, nullable=False)
    ultima_compra = Column(Date)
    proximo_lembrete = Column(Date)

    # Relacionamento com cliente
    cliente = relationship("Cliente", back_populates="pecas")

class Permissoes(Base):
    __tablename__ = "permissoes"

    id = Column(Integer, primary_key=True, index=True)
    grupo = Column(String, nullable=False)
    acao = Column(String, nullable=False)

class Usuarios(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    documento = Column(String, nullable=False)
    senha = Column(String, nullable=True)  # 👈 sugiro deixar nullable=True para convites
    grupo = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True, index=True)

    # 🔥 Nova coluna
    status = Column(String, nullable=False, default="pendente")