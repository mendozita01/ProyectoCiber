import re
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

from db import obtener_conexion

# =========================================================
# VERSION ASEGURADA - DiagNet API
#
# Cambios respecto a la version vulnerable:
# 1. El servicio ahora escucha por HTTPS (TLS) en lugar de
#    HTTP en claro, usando el certificado autofirmado del
#    laboratorio (certs/diagnet.crt y certs/diagnet.key).
#    Contramedida para: transmision en texto plano (A04) y
#    exposicion del canal a interceptacion/MITM (API10).
# 2. Se valida el formato del parametro "ip" antes de usarlo
#    en cualquier consulta (defensa adicional, aunque la
#    consulta ya usaba parametros en la version vulnerable).
# =========================================================

IP_REGEX = re.compile(
    r"^(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}$"
)


def enviar_json(handler, data, status=200):
    """
    Envia una respuesta JSON al cliente.
    """
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.end_headers()

    respuesta = json.dumps(data, ensure_ascii=False)
    handler.wfile.write(respuesta.encode("utf-8"))


class DiagNetHandler(BaseHTTPRequestHandler):
    """
    API externa DiagNet (version asegurada).

    Sigue devolviendo el mismo contrato de datos que la version
    vulnerable; el endurecimiento esta en el transporte (TLS)
    y en la validacion de entrada.
    """

    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/":
            enviar_json(self, {
                "servicio": "DiagNet API (segura)",
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
        Ruta principal de diagnostico.

        Ejemplo:
        https://localhost:8080/diagnostico?ip=192.168.1.10
        """
        parametros = parse_qs(url.query)
        ip = parametros.get("ip", [""])[0].strip()

        if not ip or not IP_REGEX.match(ip):
            enviar_json(self, {
                "error": "Debe enviar una IPv4 valida en el parametro ?ip="
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
                    "codigo_diagnostico": "IP_NOT_FOUND"
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
            # No se expone el detalle interno del error al cliente.
            print("[DiagNet] Error interno:", error)
            enviar_json(self, {
                "error": "Error interno en DiagNet"
            }, status=500)


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 8080), DiagNetHandler)

    contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto_ssl.load_cert_chain(
        certfile="../certs/diagnet.crt",
        keyfile="../certs/diagnet.key",
    )
    servidor.socket = contexto_ssl.wrap_socket(servidor.socket, server_side=True)

    print("DiagNet API (segura) corriendo en https://localhost:8080")
    print("Ejemplo: https://localhost:8080/diagnostico?ip=192.168.1.10")
    print("Si no existen los certificados, ejecute antes: bash certs/generar_certs.sh")

    servidor.serve_forever()
