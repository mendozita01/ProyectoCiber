import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# Ruta raíz del proyecto: ProyectoCiber/
ROOT_DIR = Path(__file__).resolve().parents[2]

# Cargar variables del archivo .env
load_dotenv(ROOT_DIR / ".env")


def obtener_conexion():
    """
    Crea una conexión nueva hacia PostgreSQL.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "technova"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )