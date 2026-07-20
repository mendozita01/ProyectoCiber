import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


# Ruta raíz del proyecto: ProyectoCiber/
ROOT_DIR = Path(__file__).resolve().parent.parent

# Cargar variables del archivo .env
load_dotenv(ROOT_DIR / ".env")


def obtener_conexion():
    """
    Crea una conexión nueva hacia PostgreSQL.
    DiagNet usará esta conexión para consultar la tabla diagnet_inventario_ips.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "TechNova"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )