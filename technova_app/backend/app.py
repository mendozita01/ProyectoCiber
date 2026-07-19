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

        if self.path == "/login":
            self.login()
            return

        self.responder_html("<h1>Ruta no encontrada</h1>", status=404)

    def do_GET(self):
        if self.path == "/tickets":
            self.listar_tickets()
            return

        if self.path == "/empleado-actual":
            self.empleado_actual()
            return

        if self.path == "/logout":
            self.logout()
            return

        if self.path == "/admin.html":
            empleado = self.obtener_empleado_sesion()

            if empleado is None:
                self.send_response(302)
                self.send_header("Location", "/login.html")
                self.end_headers()
                return

        super().do_GET()

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
                cursor,
                nombre,
                correo,
                telefono,
                empresa,
                ip_reportada,
                descripcion,
                estado_ticket,
                inventario_encontrado,
                nombre_equipo,
                area_equipo,
                estado_equipo,
                codigo_diagnostico,
                resultado_catalogo["mensaje_diagnostico"],
                resultado_catalogo["nivel_alerta"],
                resultado_catalogo["recomendacion"],
                latencia_ms,
            )

            conexion.commit()
            cursor.close()
            conexion.close()

            # Responder éxito
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "success", "ticket": codigo_ticket}).encode("utf-8")
            )

        except Exception as e:
            print("Error en backend:", e)
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
                "recomendacion": "Revisar manualmente el diagnóstico reportado por la API externa.",
            }

        mensaje = ""
        nivel_alerta = str(filas[0][1])
        recomendacion = str(filas[0][2])

        for fila in filas:
            mensaje += f"{fila[0]}\n"

        return {
            "mensaje_diagnostico": mensaje,
            "nivel_alerta": nivel_alerta,
            "recomendacion": recomendacion,
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
        latencia_ms,
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
                latencia_ms,
            )
        )

        codigo_ticket = cursor.fetchone()[0]
        return codigo_ticket

    def responder_html(self, contenido, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(contenido.encode("utf-8"))

    def responder_json(self, contenido, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(contenido).encode("utf-8"))

    def listar_tickets(self):
        """
        Devuelve los tickets registrados para el panel administrativo.
        """
        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT
                    codigo_ticket,
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
                    latencia_ms,
                    creado_en
                FROM tickets
                ORDER BY id DESC;
                """
            )

            filas = cursor.fetchall()

            cursor.close()
            conexion.close()

            tickets = []

            for fila in filas:
                tickets.append(
                    {
                        "codigo_ticket": fila[0],
                        "nombre_solicitante": fila[1],
                        "correo_solicitante": fila[2],
                        "telefono_solicitante": fila[3],
                        "empresa_solicitante": fila[4],
                        "ip_reportada": fila[5],
                        "descripcion_problema": fila[6],
                        "estado": fila[7],
                        "inventario_encontrado": fila[8],
                        "nombre_equipo": fila[9],
                        "area_equipo": fila[10],
                        "estado_equipo": fila[11],
                        "codigo_diagnostico": fila[12],
                        "mensaje_diagnostico": fila[13],
                        "nivel_alerta": fila[14],
                        "recomendacion": fila[15],
                        "latencia_ms": fila[16],
                        "creado_en": str(fila[17]),
                    }
                )

            self.responder_json({"status": "ok", "tickets": tickets})

        except Exception as error:
            self.responder_json(
                {
                    "status": "error",
                    "mensaje": "Error consultando tickets",
                    "detalle": str(error),
                },
                status=500,
            )

    def login(self):
        """
        Login de empleados TechNova.
        En esta rama vulnerable se compara la contraseña usando MD5.
        """

        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = parse_qs(post_data)

            usuario = params.get("usuario", [""])[0].strip()
            password = params.get("password", [""])[0].strip()

            if not usuario or not password:
                self.responder_html(
                    "<h1>Error</h1><p>Debe ingresar usuario y contraseña.</p><a href='/login.html'>Volver</a>",
                    status=400,
                )
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT id, nombre, apellido, usuario, tipo_empleado
                FROM empleados
                WHERE usuario = %s
                  AND password_hash = MD5(%s)
                  AND activo = TRUE;
                """,
                (usuario, password),
            )

            empleado = cursor.fetchone()

            cursor.close()
            conexion.close()

            if empleado is None:
                self.responder_html(
                    "<h1>Acceso denegado</h1><p>Usuario o contraseña incorrectos.</p><a href='/login.html'>Volver</a>",
                    status=401,
                )
                return

            empleado_id = empleado[0]

            self.send_response(302)
            self.send_header("Location", "/admin.html")
            self.send_header("Set-Cookie", f"empleado_id={empleado_id}; Path=/")
            self.end_headers()

        except Exception as error:
            self.responder_html(
                f"""
                <h1>Error en login</h1>
                <p>{str(error)}</p>
                <a href="/login.html">Volver</a>
                """,
                status=500,
            )

    def obtener_empleado_sesion(self):
        """
        Busca el empleado que inició sesión usando la cookie empleado_id.
        """

        cookie = self.headers.get("Cookie", "")
        empleado_id = None

        for parte in cookie.split(";"):
            parte = parte.strip()

            if parte.startswith("empleado_id="):
                empleado_id = parte.replace("empleado_id=", "")
                break

        if not empleado_id:
            return None

        try:
            conexion = obtener_conexion()
            cursor = conexion.cursor()

            cursor.execute(
                """
                SELECT id, nombre, apellido, correo, usuario, tipo_empleado
                FROM empleados
                WHERE id = %s
                AND activo = TRUE;
                """,
                (empleado_id,),
            )

            empleado = cursor.fetchone()

            cursor.close()
            conexion.close()

            if empleado is None:
                return None

            return {
                "id": empleado[0],
                "nombre": empleado[1],
                "apellido": empleado[2],
                "correo": empleado[3],
                "usuario": empleado[4],
                "tipo_empleado": empleado[5],
            }

        except Exception:
            return None

    def empleado_actual(self):
        """
        Envía al panel los datos del empleado que inició sesión.
        """

        empleado = self.obtener_empleado_sesion()

        if empleado is None:
            self.responder_json(
                {
                    "status": "error",
                    "mensaje": "No hay empleado con sesión activa",
                },
                status=401,
            )
            return

        self.responder_json({
            "status": "ok",
            "empleado": empleado,
        })

    def logout(self):
        """
        Cierra la sesión del empleado.
        """

        self.send_response(302)
        self.send_header("Location", "/login.html")
        self.send_header("Set-Cookie", "empleado_id=; Path=/; Max-Age=0")
        self.end_headers()


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 3000), TechNovaHandler)

    print("TechNova App vulnerable corriendo en http://localhost:3000 o http://127.0.0.1:3000")
    print("Debe estar activa la API DiagNet en http://localhost:8080")

    servidor.serve_forever()