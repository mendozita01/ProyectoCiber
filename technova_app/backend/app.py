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
            params = parse_qs(post_data)

            ip_reportada = params.get("ip_reportada", [""])[0].strip()

            if not ip_reportada:
                self.responder_html(
                    "<h1>Error</h1><p>Debe ingresar una IP.</p>",
                    status=400
                )
                return

            # Datos temporales hasta conectar el formulario completo.
            nombre_solicitante = "Solicitante de prueba"
            correo_solicitante = "sin-correo@cliente.local"
            telefono_solicitante = ""
            empresa_solicitante = "Empresa cliente"
            descripcion_problema = "Solicitud de revisión de conectividad para la IP reportada."

            # 1. Consultar API externa DiagNet.
            datos_api = self.consultar_diagnet(ip_reportada)

            inventario_encontrado = datos_api.get("inventario_encontrado")
            nombre_equipo = datos_api.get("nombre_equipo", "")
            area_equipo = datos_api.get("area", "")
            estado_equipo = datos_api.get("estado_equipo", "")
            latencia_ms = datos_api.get("latencia_ms")
            codigo_diagnostico = datos_api.get("codigo_diagnostico", "ERROR_API")

            if inventario_encontrado is True:
                estado_ticket = "diagnosticado"
            else:
                estado_ticket = "en_revision"

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # 2. Punto vulnerable: el código recibido desde DiagNet
            # se usa directamente dentro de una consulta SQL.
            resultado_catalogo = self.consultar_catalogo_vulnerable(
                cursor,
                codigo_diagnostico
            )

            mensaje_diagnostico = resultado_catalogo["mensaje_diagnostico"]
            nivel_alerta = resultado_catalogo["nivel_alerta"]
            recomendacion = resultado_catalogo["recomendacion"]

            # 3. Guardar ticket.
            codigo_ticket = self.guardar_ticket(
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
            )

            conexion.commit()
            cursor.close()
            conexion.close()

            html = f"""
            <h1>Ticket creado correctamente</h1>

            <p><strong>Código del ticket:</strong> {codigo_ticket}</p>
            <p><strong>IP reportada:</strong> {ip_reportada}</p>
            <p><strong>Estado del ticket:</strong> {estado_ticket}</p>

            <h3>Datos recibidos desde DiagNet</h3>
            <p><strong>Inventario encontrado:</strong> {inventario_encontrado}</p>
            <p><strong>Equipo:</strong> {nombre_equipo}</p>
            <p><strong>Área:</strong> {area_equipo}</p>
            <p><strong>Estado del equipo:</strong> {estado_equipo}</p>
            <p><strong>Latencia:</strong> {latencia_ms}</p>
            <p><strong>Código diagnóstico:</strong> {codigo_diagnostico}</p>

            <h3>Diagnóstico interpretado por TechNova</h3>
            <pre>{mensaje_diagnostico}</pre>
            <p><strong>Nivel de alerta:</strong> {nivel_alerta}</p>
            <p><strong>Recomendación:</strong> {recomendacion}</p>

            <br>
            <a href="/">Crear otro ticket</a>
            """

            self.responder_html(html)

        except Exception as error:
            self.responder_html(
                f"""
                <h1>Error creando el ticket</h1>
                <p>{str(error)}</p>
                """,
                status=500
            )

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