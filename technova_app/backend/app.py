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
            
        # NUEVAS RUTAS PARA LA GESTIÓN DE TICKETS
        if self.path == "/cambiar_estado":
            self.cambiar_estado()
            return
            
        if self.path == "/asignar_ticket":
            self.asignar_ticket()
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

        if self.path.startswith("/consultar_ticket"):
            self.consultar_ticket()
            return
        
        if self.path.startswith("/admin.html"):
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

            # Acceso directo al diccionario
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
        Error intencional: codigo_diagnostico se concatena directamente.
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

    def consultar_ticket(self):
        """
        Devuelve la información de un ticket específico para que el usuario (o atacante)
        pueda ver el resultado del diagnóstico.
        """
        from urllib.parse import urlparse, parse_qs
        
        try:
            url = urlparse(self.path)
            parametros = parse_qs(url.query)
            codigo_ticket = parametros.get("ticket", [""])[0].strip()

            if not codigo_ticket:
                self.responder_json({"error": "Debe enviar el código del ticket"}, status=400)
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # Consultamos los datos del ticket. El campo 'mensaje_diagnostico'
            # es donde se reflejarán los hashes si hubo una Inyección SQL.
            cursor.execute(
                """
                SELECT 
                    codigo_ticket, 
                    estado, 
                    ip_reportada, 
                    codigo_diagnostico,
                    mensaje_diagnostico, 
                    nivel_alerta, 
                    recomendacion,
                    creado_en
                FROM tickets
                WHERE codigo_ticket = %s;
                """,
                (codigo_ticket,)
            )

            fila = cursor.fetchone()
            cursor.close()
            conexion.close()

            if not fila:
                self.responder_json({"error": "Ticket no encontrado"}, status=404)
                return

            datos_ticket = {
                "codigo_ticket": fila[0],
                "estado": fila[1],
                "ip_reportada": fila[2],
                "codigo_diagnostico": fila[3],
                "mensaje_diagnostico": fila[4], # <- ¡Aquí se verán los hashes robados!
                "nivel_alerta": fila[5],
                "recomendacion": fila[6],
                "creado_en": str(fila[7])
            }

            self.responder_json(datos_ticket)

        except Exception as error:
            print("Error consultando ticket individual:", error)
            self.responder_json({"error": "Error interno del servidor", "detalle": str(error)}, status=500)            

    def login(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            
            params = json.loads(post_data)
            usuario = params.get("usuario", "").strip()
            password = params.get("password", "").strip()

            if not usuario or not password:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Datos Incompletos"}).encode("utf-8"))
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # PASO 1: Verificamos si el usuario existe
            cursor.execute("SELECT id FROM empleados WHERE usuario = %s AND activo = TRUE", (usuario,))
            usuario_existe = cursor.fetchone()

            login_valido = None
            
            if not usuario_existe:
                respuesta = {"status": "error", "message": "Usuario No Autorizado"}
            else:
                # PASO 2: Validamos la contraseña
                cursor.execute("""
                    SELECT id, nombre, tipo_empleado 
                    FROM empleados 
                    WHERE usuario = %s AND password_hash = MD5(%s) AND activo = TRUE
                """, (usuario, password))
                login_valido = cursor.fetchone()

                if not login_valido:
                    respuesta = {"status": "error", "message": "Contraseña Inválida"}
                else:
                    respuesta = {"status": "success"}

            cursor.close()
            conexion.close()

            # PASO 3: ENVIAR RESPUESTA Y COOKIE
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            
            # Si el login fue exitoso, configuramos la cookie
            if login_valido:
                empleado_id = login_valido[0]
                self.send_header("Set-Cookie", f"empleado_id={empleado_id}; Path=/; HttpOnly")

            self.end_headers()
            self.wfile.write(json.dumps(respuesta).encode("utf-8"))

        except Exception as e:
            print("Error en login:", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Servidor No Disponible. Intente más tarde."}).encode("utf-8"))

    def cambiar_estado(self):
        """
        Cambia el estado de un ticket directamente desde el lapicito del modal.
        """
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id")
            nuevo_estado = params.get("nuevo_estado")

            if codigo_ticket and nuevo_estado:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute(
                    "UPDATE tickets SET estado = %s, actualizado_en = CURRENT_TIMESTAMP WHERE codigo_ticket = %s",
                    (nuevo_estado, codigo_ticket)
                )
                conexion.commit()
                cursor.close()
                conexion.close()

            self.responder_json({"status": "ok"})
        except Exception as e:
            print("Error cambiando estado:", e)
            self.responder_json({"status": "error"}, status=500)

    def asignar_ticket(self):
        """
        Simula el envío de un correo y cambia el estado del ticket a 'asignado'.
        """
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id")
            analista_correo = params.get("analista")
            mensaje = params.get("mensaje")

            # Simulamos que se envió el correo imprimiéndolo en consola
            print(f"\n[+] SIMULACIÓN DE CORREO ENVIADO:")
            print(f"    Para: {analista_correo}")
            print(f"    Ticket: {codigo_ticket}")
            print(f"    Instrucciones: {mensaje}\n")

            if codigo_ticket:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                # Lo pasamos automáticamente a estado 'asignado'
                cursor.execute(
                    "UPDATE tickets SET estado = 'asignado', actualizado_en = CURRENT_TIMESTAMP WHERE codigo_ticket = %s",
                    (codigo_ticket,)
                )
                conexion.commit()
                cursor.close()
                conexion.close()

            self.responder_json({"status": "ok"})
        except Exception as e:
            print("Error asignando ticket:", e)
            self.responder_json({"status": "error"}, status=500)

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
                    "mensaje": "No Hay Empleado Con Sesión Activa",
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