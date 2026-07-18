from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, quote
import urllib.request
import json

from db import obtener_conexion


class TechNovaHandler(SimpleHTTPRequestHandler):
    """
    Backend vulnerable de TechNova.

    Idea principal:
    TechNova consulta la API externa DiagNet y usa el codigo_diagnostico
    recibido para buscar información en su catálogo interno.

    Vulnerabilidad:
    el codigo_diagnostico viene de una API externa y se concatena
    directamente en una consulta SQL.

    Esto representa:
    - Consumo inseguro de APIs.
    - SQL Injection.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="../frontend", **kwargs)

    def do_POST(self):
        if self.path == "/crear_ticket":
            self.crear_ticket()
            return

        self.responder_html("<h1>Ruta no encontrada</h1>", status=404)

    def crear_ticket(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            # Recibimos el JSON
            params = json.loads(post_data)
            
            # Debug: Imprimir en la consola de Python para ver qué llega
            print("Datos recibidos en backend:", params)

            # Acceso directo al diccionario (sin usar [0] porque ya no es una lista)
            ip_reportada = params.get("ip_reportada", "").strip()

            if not ip_reportada:
                self.send_response(400)
                self.end_headers()
                return

            # Asignación segura de datos desde el JSON
            nombre = params.get("nombre_solicitante", "Anónimo")
            correo = params.get("correo_solicitante", "sin@correo.com")
            telefono = params.get("telefono_solicitante", "")
            empresa = params.get("empresa_solicitante", "")
            descripcion = params.get("descripcion_problema", "")

            # 1. Consultar API externa
            datos_api = self.consultar_diagnet(ip_reportada)
            
            inventario_encontrado = datos_api.get("inventario_encontrado")
            nombre_equipo = datos_api.get("nombre_equipo", "")
            area_equipo = datos_api.get("area", "")
            estado_equipo = datos_api.get("estado_equipo", "")
            latencia_ms = datos_api.get("latencia_ms")
            codigo_diagnostico = datos_api.get("codigo_diagnostico", "ERROR_API")

            estado_ticket = "diagnosticado" if inventario_encontrado else "en_revision"

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # Diagnóstico (VULNERABLE A SQLI - MANTENEMOS ASÍ PARA LA DEMO)
            resultado_catalogo = self.consultar_catalogo_vulnerable(cursor, codigo_diagnostico)

            # Guardar en BD
            codigo_ticket = self.guardar_ticket(
                cursor, nombre, correo, telefono, empresa, ip_reportada, 
                descripcion, estado_ticket, inventario_encontrado, 
                nombre_equipo, area_equipo, estado_equipo, codigo_diagnostico,
                resultado_catalogo["mensaje_diagnostico"],
                resultado_catalogo["nivel_alerta"],
                resultado_catalogo["recomendacion"],
                latencia_ms
            )

            conexion.commit()
            cursor.close()
            conexion.close()

            # Responder éxito
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "ticket": codigo_ticket}).encode("utf-8"))

        except Exception as e:
            print("Error en backend:", e) # Esto imprimirá el error real en tu terminal
            self.send_response(500)
            self.end_headers()

    def consultar_diagnet(self, ip_reportada):
        """
        Consulta DiagNet.
        Ejemplo: http://localhost:8080/diagnostico?ip=192.168.1.10
        """

        ip_codificada = quote(ip_reportada)
        url_diagnet = f"http://localhost:8080/diagnostico?ip={ip_codificada}"

        with urllib.request.urlopen(url_diagnet) as response:
            respuesta_api = response.read().decode("utf-8")
            datos_api = json.loads(respuesta_api)

        return datos_api

    def consultar_catalogo_vulnerable(self, cursor, codigo_diagnostico):
        """
        Busca el código diagnóstico en el catálogo interno.

        Error intencional:
        codigo_diagnostico viene desde DiagNet y se concatena en el SQL.
        """

        consulta = f"""
            SELECT
                descripcion,
                nivel_alerta,
                recomendacion
            FROM catalogo_diagnosticos
            WHERE codigo = '{codigo_diagnostico}';
        """

        print("Consulta SQL ejecutada:")
        print(consulta)

        cursor.execute(consulta)
        filas = cursor.fetchall()

        if not filas:
            return {
                "mensaje_diagnostico": "No se encontró información para el código diagnóstico recibido.",
                "nivel_alerta": "media",
                "recomendacion": "Revisar manualmente el diagnóstico reportado por la API externa."
            }

        mensaje = ""
        nivel_alerta = str(filas[0][1])
        recomendacion = str(filas[0][2])

        for fila in filas:
            mensaje += f"{fila}\n"

        return {
            "mensaje_diagnostico": mensaje,
            "nivel_alerta": nivel_alerta,
            "recomendacion": recomendacion
        }

    def guardar_ticket(
        self,
        cursor,
        nombre_solicitante,
        correo_solicitante,
        telefono_solicitante,
        empresa_solicitante,
        ip_reportada,
        descripcion_problema,
        estado_ticket,
        inventario_encontrado,
        nombre_equipo,
        area_equipo,
        estado_equipo,
        codigo_diagnostico,
        mensaje_diagnostico,
        nivel_alerta,
        recomendacion,
        latencia_ms
    ):
        """
        Guarda el ticket con los datos recibidos e interpretados.
        """

        cursor.execute(
            """
            INSERT INTO tickets (
                nombre_solicitante,
                correo_solicitante,
                telefono_solicitante,
                empresa_solicitante,
                ip_reportada,
                descripcion_problema,
                estado,
                inventario_encontrado,
                nombre_equipo,
                area_equipo,
                estado_equipo,
                codigo_diagnostico,
                mensaje_diagnostico,
                nivel_alerta,
                recomendacion,
                latencia_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING codigo_ticket;
            """,
            (
                nombre_solicitante,
                correo_solicitante,
                telefono_solicitante,
                empresa_solicitante,
                ip_reportada,
                descripcion_problema,
                estado_ticket,
                inventario_encontrado,
                nombre_equipo,
                area_equipo,
                estado_equipo,
                codigo_diagnostico[:250],
                mensaje_diagnostico,
                nivel_alerta,
                recomendacion,
                latencia_ms
            )
        )

        codigo_ticket = cursor.fetchone()[0]
        return codigo_ticket

    def responder_html(self, contenido, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenido.encode("utf-8"))


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 3000), TechNovaHandler)

    print("TechNova App vulnerable corriendo en http://localhost:3000")
    print("Debe estar activa la API DiagNet en http://localhost:8080")

    servidor.serve_forever()