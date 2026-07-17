from db import obtener_conexion

try:
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM empleados;")
    total_empleados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tickets;")
    total_tickets = cursor.fetchone()[0]

    print("Conexión exitosa con PostgreSQL")
    print(f"Total empleados: {total_empleados}")
    print(f"Total tickets: {total_tickets}")

    cursor.close()
    conexion.close()

except Exception as error:
    print("Error conectando a PostgreSQL:")
    print(error)