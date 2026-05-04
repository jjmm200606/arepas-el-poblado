"""
Conexión a PostgreSQL - Sin crear tablas (ya existen en la BD)
"""
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine, event, text
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


def _sanitizar_database_url(database_url: str) -> str:
    """Quita parámetros incompatibles con el pooler de Neon."""
    partes = urlsplit(database_url)
    if not partes.query:
        return database_url

    query = []
    for key, value in parse_qsl(partes.query, keep_blank_values=True):
        if key == "options" and "search_path" in value:
            continue
        query.append((key, value))

    return urlunsplit(
        (partes.scheme, partes.netloc, partes.path, urlencode(query), partes.fragment)
    )


DATABASE_URL = _sanitizar_database_url(DATABASE_URL)

# Crear engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)


@event.listens_for(engine, "connect")
def _configurar_search_path(dbapi_connection, connection_record):
    """Fuerza el schema public para conexiones que no traen search_path por defecto."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET search_path TO public")
    finally:
        cursor.close()


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
