"""
Conexión a PostgreSQL - Sin crear tablas (ya existen en la BD)
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# URL de conexión a PostgreSQL
# Railway entrega "postgres://..." — SQLAlchemy necesita "postgresql://..."
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/arepas_el_poblado"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)


# Base para los modelos ORM
Base = declarative_base()

# Session para consultas
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Dependencia para obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Verificar que la conexión funciona"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexión a PostgreSQL OK")
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False
