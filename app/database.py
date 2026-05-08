"""
Conexion a base de datos para la aplicacion.

Soporta PostgreSQL y Oracle a traves de SQLAlchemy usando DATABASE_URL.
"""
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from pathlib import Path
import base64
import tempfile
import zipfile
from io import BytesIO

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=True)

# URL de conexion.
# Ejemplos:
# - PostgreSQL: postgresql://usuario:password@host:5432/base
# - Oracle: oracle+oracledb://usuario:password@host:1521/?service_name=servicio
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
DATABASE_BACKEND = urlsplit(DATABASE_URL).scheme.lower()


def _es_oracle(url: str) -> bool:
    esquema = urlsplit(url).scheme.lower()
    return esquema.startswith("oracle")


def _es_postgres(url: str) -> bool:
    esquema = urlsplit(url).scheme.lower()
    return esquema.startswith("postgresql")


def _resolver_wallet_oracle():
    wallet_b64 = os.getenv("ORACLE_WALLET_B64")
    if not wallet_b64:
        return None

    wallet_dir = Path(tempfile.gettempdir()) / "oracle_wallet_runtime"
    if not wallet_dir.exists() or not any(wallet_dir.iterdir()):
        wallet_dir.mkdir(parents=True, exist_ok=True)
        contenido = base64.b64decode(wallet_b64)
        with zipfile.ZipFile(BytesIO(contenido)) as zip_ref:
            zip_ref.extractall(wallet_dir)
    return wallet_dir


engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
}

database_url_for_engine = DATABASE_URL

if _es_oracle(DATABASE_URL):
    # future=True ayuda a mantener el comportamiento uniforme con SQLAlchemy 2.
    engine_kwargs["future"] = True
    oracle_connect_args = {}

    oracle_user = os.getenv("ORACLE_USER")
    oracle_password = os.getenv("ORACLE_PASSWORD")
    oracle_dsn = os.getenv("ORACLE_DSN")
    oracle_config_dir = os.getenv("ORACLE_CONFIG_DIR")
    oracle_wallet_location = os.getenv("ORACLE_WALLET_LOCATION")
    oracle_wallet_password = os.getenv("ORACLE_WALLET_PASSWORD")
    oracle_wallet_runtime_dir = _resolver_wallet_oracle()

    if oracle_user and oracle_password:
        database_url_for_engine = URL.create(
            "oracle+oracledb",
            username=oracle_user,
            password=oracle_password,
        )

    if oracle_dsn:
        oracle_connect_args["dsn"] = oracle_dsn
    if oracle_wallet_runtime_dir:
        oracle_config_dir = str(oracle_wallet_runtime_dir)
        oracle_wallet_location = str(oracle_wallet_runtime_dir)
    if oracle_config_dir:
        oracle_connect_args["config_dir"] = oracle_config_dir
    if oracle_wallet_location:
        oracle_connect_args["wallet_location"] = oracle_wallet_location
    if oracle_wallet_password:
        oracle_connect_args["wallet_password"] = oracle_wallet_password

    if oracle_connect_args:
        engine_kwargs["connect_args"] = oracle_connect_args

# Crear engine
engine = create_engine(database_url_for_engine, **engine_kwargs)


@event.listens_for(engine, "connect")
def _configurar_search_path(dbapi_connection, connection_record):
    """Ajustes por motor al abrir cada conexion."""
    if not _es_postgres(DATABASE_URL):
        return
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
            consulta = "SELECT 1 FROM DUAL" if _es_oracle(DATABASE_URL) else "SELECT 1"
            result = conn.execute(text(consulta))
            motor = "Oracle" if _es_oracle(DATABASE_URL) else "PostgreSQL"
            print(f"Conexion a {motor} OK")
            return True
    except Exception as e:
        print(f"Error de conexion: {e}")
        return False
