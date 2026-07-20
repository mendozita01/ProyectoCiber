"""
Utilidad para generar un hash bcrypt a partir de una contraseña en texto
plano. Util para actualizar database/insert.sql con nuevos usuarios o
nuevas contraseñas de demo, sin depender de funciones inseguras como
MD5() dentro del propio motor de base de datos.

Uso:
    python3 generar_hash.py "MiContraseñaSegura"
"""
import sys
import bcrypt

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 generar_hash.py \"contraseña\"")
        sys.exit(1)

    contrasena = sys.argv[1].encode("utf-8")
    hash_generado = bcrypt.hashpw(contrasena, bcrypt.gensalt(rounds=12))
    print(hash_generado.decode("utf-8"))
