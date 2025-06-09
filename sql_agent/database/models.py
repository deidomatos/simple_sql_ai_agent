from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clientes'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    saldo = Column(Float, default=0.0)
    data_cadastro = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship: One client can have many transactions
    transacoes = relationship("Transacao", back_populates="cliente")
    
    def __repr__(self):
        return f"<Cliente(id={self.id}, nome='{self.nome}', email='{self.email}', saldo={self.saldo})>"


class Produto(Base):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    descricao = Column(String)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0)
    
    # Relationship: One product can be in many transactions
    transacoes = relationship("Transacao", back_populates="produto")
    
    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', preco={self.preco}, estoque={self.estoque})>"


class Transacao(Base):
    __tablename__ = 'transacoes'
    
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    quantidade = Column(Integer, nullable=False, default=1)
    valor_total = Column(Float, nullable=False)
    data_transacao = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    cliente = relationship("Cliente", back_populates="transacoes")
    produto = relationship("Produto", back_populates="transacoes")
    
    def __repr__(self):
        return f"<Transacao(id={self.id}, cliente_id={self.cliente_id}, produto_id={self.produto_id}, valor_total={self.valor_total})>"


def init_db(db_url):
    """Initialize the database with the defined models"""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine