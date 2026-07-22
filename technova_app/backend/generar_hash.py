"""
Utilidad para generar un hash PBKDF2-HMAC-SHA256 a partir de una
contraseña en texto plano.

Uso:
    python generar_hash.py "admin12"

Este archivo se usa para preparar valores de prueba en database/insert.sql.
No se utiliza para iniciar sesión; el login verifica los hashes desde app.py.
"""

import sys
import hashlib
import secrets


ITERACIONES_HASH = 150000


def generar_hash_password(password):
    """
    Genera un hash seguro de contraseña con salt único.

    Formato generado:
    pbkdf2_sha256$iteraciones$salt$hash
    """
    salt = secrets.token_hex(16)

    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERACIONES_HASH
    )

    hash_hex = hash_bytes.hex()
    return f"pbkdf2_sha256${ITERACIONES_HASH}${salt}${hash_hex}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Uso: python generar_hash.py "contraseña"')
        sys.exit(1)

    password = sys.argv[1]
    print(generar_hash_password(password))