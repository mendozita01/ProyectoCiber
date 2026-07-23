from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

from db import obtener_conexion


def enviar_json(handler, data, status=200):
    """
    Envía una respuesta JSON al cliente.
    """

    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.end_headers()

    respuesta = json.dumps(data, ensure_ascii=False)
    handler.wfile.write(respuesta.encode("utf-8"))


class DiagNetHandler(BaseHTTPRequestHandler):
    """
    API externa DiagNet.

    Esta API recibe una IP y devuelve datos técnicos del equipo.
    TechNova usará esos datos para crear el ticket.
    """

    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/":
            enviar_json(self, {
                "servicio": "DiagNet API",
                "estado": "activo"
            })
            return

        if url.path == "/diagnostico":
            self.diagnostico(url)
            return

        enviar_json(self, {
            "error": "Ruta no encontrada"
        }, status=404)

    def diagnostico(self, url):
        """
        Ruta principal de diagnóstico.

        Ejemplo:
        http://localhost:8080/diagnostico?ip=192.168.1.10
        """

        parametros = parse_qs(url.query)
        ip = parametros.get("ip", [""])[0].strip()

        if not ip:
            enviar_json(self, {
                "error": "Debe enviar una IP en el parámetro ?ip="
            }, status=400)
            return

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT
                    ip,
                    nombre_equipo,
                    area,
                    estado_equipo,
                    latencia_ms,
                    codigo_diagnostico
                FROM diagnet_inventario_ips
                WHERE ip = %s
                  AND activo = TRUE;
                """,
                (ip,)
            )

            equipo = cursor.fetchone()

            cursor.close()
            conexion.close()

            if equipo is None:
                enviar_json(self, {
                    "ip_consultada": ip,
                    "inventario_encontrado": False,
                    "nombre_equipo": "",
                    "area": "",
                    "estado_equipo": "desconocido",
                    "latencia_ms": None,
                    "codigo_diagnostico": codigo_diagnostico
                })
                return

            (
                ip_encontrada,
                nombre_equipo,
                area,
                estado_equipo,
                latencia_ms,
                codigo_diagnostico
            ) = equipo 

            enviar_json(self, {
                "ip_consultada": ip_encontrada,
                "inventario_encontrado": True,
                "nombre_equipo": nombre_equipo,
                "area": area,
                "estado_equipo": estado_equipo,
                "latencia_ms": latencia_ms,
                "codigo_diagnostico": codigo_diagnostico
            })

        except Exception as error:
            enviar_json(self, {
                "error": "Error interno en DiagNet",
                "detalle": str(error)
            }, status=500)


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", 8080), DiagNetHandler)

    print("DiagNet API corriendo en http://0.0.0.0:8080")
    print("Ejemplo desde otra maquina: http://IP_DIAGNET:8080/diagnostico?ip=192.168.1.10")

    servidor.serve_forever()