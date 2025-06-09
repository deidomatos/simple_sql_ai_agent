from sqlalchemy.orm import sessionmaker
from .models import Cliente, Produto, Transacao, Base
from .connection import engine
import datetime
import random

def seed_database():
    """Seed the database with sample data"""
    # Create tables
    Base.metadata.create_all(engine)
    
    # Create a session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Check if data already exists
        if session.query(Cliente).count() > 0:
            print("Database already seeded. Skipping...")
            return
        
        # Create sample clients
        clientes = [
            Cliente(nome="João Silva", email="joao.silva@example.com", saldo=5000.0),
            Cliente(nome="Maria Oliveira", email="maria.oliveira@example.com", saldo=3500.0),
            Cliente(nome="Pedro Santos", email="pedro.santos@example.com", saldo=2000.0),
            Cliente(nome="Ana Costa", email="ana.costa@example.com", saldo=7500.0),
            Cliente(nome="Carlos Ferreira", email="carlos.ferreira@example.com", saldo=1000.0),
            Cliente(nome="Lucia Pereira", email="lucia.pereira@example.com", saldo=4500.0),
            Cliente(nome="Roberto Almeida", email="roberto.almeida@example.com", saldo=6000.0),
            Cliente(nome="Fernanda Lima", email="fernanda.lima@example.com", saldo=3000.0),
            Cliente(nome="Bruno Martins", email="bruno.martins@example.com", saldo=2500.0),
            Cliente(nome="Juliana Rocha", email="juliana.rocha@example.com", saldo=8000.0)
        ]
        
        session.add_all(clientes)
        session.commit()
        
        # Create sample products
        produtos = [
            Produto(nome="Notebook", descricao="Notebook de alta performance", preco=4500.0, estoque=10),
            Produto(nome="Smartphone", descricao="Smartphone com câmera de alta resolução", preco=2500.0, estoque=20),
            Produto(nome="Tablet", descricao="Tablet com tela de 10 polegadas", preco=1800.0, estoque=15),
            Produto(nome="Monitor", descricao="Monitor de 27 polegadas", preco=1200.0, estoque=8),
            Produto(nome="Teclado", descricao="Teclado mecânico", preco=350.0, estoque=30),
            Produto(nome="Mouse", descricao="Mouse sem fio", preco=120.0, estoque=25),
            Produto(nome="Headphone", descricao="Headphone com cancelamento de ruído", preco=800.0, estoque=12),
            Produto(nome="Impressora", descricao="Impressora multifuncional", preco=950.0, estoque=5),
            Produto(nome="Webcam", descricao="Webcam HD", preco=280.0, estoque=18),
            Produto(nome="HD Externo", descricao="HD Externo 1TB", preco=400.0, estoque=22)
        ]
        
        session.add_all(produtos)
        session.commit()
        
        # Create sample transactions
        # Generate 30 random transactions
        for _ in range(30):
            cliente = random.choice(clientes)
            produto = random.choice(produtos)
            quantidade = random.randint(1, 3)
            valor_total = produto.preco * quantidade
            
            # Create transaction with a random date in the last 30 days
            days_ago = random.randint(0, 30)
            transaction_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
            
            transacao = Transacao(
                cliente_id=cliente.id,
                produto_id=produto.id,
                quantidade=quantidade,
                valor_total=valor_total,
                data_transacao=transaction_date
            )
            
            session.add(transacao)
        
        # Add some specific transactions for testing the example questions
        # 1. Make sure some clients bought notebooks
        notebook = session.query(Produto).filter_by(nome="Notebook").first()
        for cliente in [clientes[0], clientes[3], clientes[6]]:  # João, Ana, Roberto
            transacao = Transacao(
                cliente_id=cliente.id,
                produto_id=notebook.id,
                quantidade=1,
                valor_total=notebook.preco,
                data_transacao=datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 15))
            )
            session.add(transacao)
        
        # 2. Make sure some clients have enough balance for a smartphone
        # This is already handled by the client balances we set
        
        session.commit()
        print("Database seeded successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()