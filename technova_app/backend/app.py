import logging
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote
import urllib.request
import json

import bcrypt

from db import obtener_conexion

# =========================================================
# VERSION ASEGURADA - Backend de TechNova
#
# Resumen de contramedidas aplicadas frente a la version
# vulnerable (ver comentarios "VULNERABLE" en la rama
# version-vulnerable para el contraste linea a linea):
#
# 1) API10 - Consumo No Seguro de APIs
#    - Se valida el esquema completo del JSON que devuelve
#      DiagNet (claves esperadas + tipos) antes de usarlo.
#    - "codigo_diagnostico" se valida contra una lista blanca
#      de valores permitidos; cualquier otro valor se trata
#      como invalido y NUNCA llega a la consulta SQL.
#    - La consulta al catalogo usa parametros (%s), nunca
#      concatenacion de strings.
#    - El canal hacia DiagNet ahora es HTTPS y TechNova valida
#      la identidad de DiagNet contra su certificado conocido
#      (certificate pinning), por lo que un servidor suplantado
#      con otro certificado sera rechazado.
#
# 2) A04 - Fallas Criptograficas
#    - Las contrasenas se verifican con bcrypt (hash + salt
#      individual por usuario), no con MD5 sin salt.
#    - El servidor de TechNova ahora sirve por HTTPS, por lo
#      que las credenciales del formulario /login ya no viajan
#      en texto plano.
#    - Los mensajes de error del login son genericos (no se
#      revela si el usuario existe o no, evitando enumeracion
#      de usuarios).
#    - Los errores internos (excepciones, detalle SQL) ya no
#      se envian al cliente; se registran solo en el log del
#      servidor.
# =========================================================

logging.basicConfig(
    filename="technova_seguro.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# --- Lista blanca de codigos de diagnostico validos (API10) ---
# Debe coincidir con los codigos reales de catalogo_diagnosticos.
CODIGOS_DIAGNOSTICO_VALIDOS = {
    "OK-200",
    "HIGH_LATENCY",
    "HOST_DOWN",
    "IP_NOT_FOUND",
    "TIMEOUT",
}

# --- Esquema esperado de la respuesta de DiagNet (API10) ---
# clave -> tupla de tipos python aceptados
ESQUEMA_DIAGNET = {
    "ip_consultada": (str,),
    "inventario_encontrado": (bool,),
    "nombre_equipo": (str,),
    "area": (str,),
    "estado_equipo": (str,),
    "latencia_ms": (int, type(None)),
    "codigo_diagnostico": (str,),
}


class RespuestaDiagNetInvalida(Exception):
    """Se lanza cuando la respuesta de DiagNet no pasa la validacion de esquema."""
    pass


def validar_respuesta_diagnet(datos):
    """
    Valida que la respuesta de DiagNet:
    1. Sea un objeto JSON (dict).
    2. Contenga exactamente las claves esperadas, con el tipo correcto.
    3. Tenga un codigo_diagnostico dentro de la lista blanca.

    Esta es la contramedida central para API10: en la version
    vulnerable, este objeto se usaba "tal cual" sin ninguna de
    estas verificaciones.
    """
    if not isinstance(datos, dict):
        raise RespuestaDiagNetInvalida("La respuesta de DiagNet no es un objeto JSON valido.")

    for clave, tipos_aceptados in ESQUEMA_DIAGNET.items():
        if clave not in datos:
            raise RespuestaDiagNetInvalida(f"Falta la clave esperada '{clave}' en la respuesta de DiagNet.")
        if not isinstance(datos[clave], tipos_aceptados):
            raise RespuestaDiagNetInvalida(
                f"Tipo invalido para '{clave}': se esperaba {tipos_aceptados}, llego {type(datos[clave])}."
            )

    if datos["codigo_diagnostico"] not in CODIGOS_DIAGNOSTICO_VALIDOS:
        raise RespuestaDiagNetInvalida(
            f"codigo_diagnostico '{datos['codigo_diagnostico']}' no pertenece a la lista blanca permitida."
        )

    return datos


class TechNovaHandler(SimpleHTTPRequestHandler):
    """
    Backend asegurado de TechNova.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="../frontend", **kwargs)

    def do_POST(self):
        if self.path == "/crear_ticket":
            self.crear_ticket()
            return

        if self.path == "/consultar_ticket":
            self.consultar_ticket()
            return

        if self.path == "/login":
            self.login()
            return

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
            params = json.loads(post_data)

            ip_reportada = params.get("ip_reportada", "").strip()

            if not ip_reportada:
                self.send_response(400)
                self.end_headers()
                return

            nombre = params.get("nombre_solicitante", "Anónimo")
            correo = params.get("correo_solicitante", "sin@correo.com")
            telefono = params.get("telefono_solicitante", "")
            empresa = params.get("empresa_solicitante", "")
            descripcion = params.get("descripcion_problema", "")

            # 1. Consultar API externa (ahora por HTTPS + pinning)
            try:
                datos_api = self.consultar_diagnet(ip_reportada)
                datos_api = validar_respuesta_diagnet(datos_api)
            except RespuestaDiagNetInvalida as error:
                # La respuesta no paso la validacion de esquema/lista blanca.
                # Se registra el detalle solo en el log del servidor y se
                # continua el flujo tratando el diagnostico como no disponible,
                # sin exponer el motivo tecnico al cliente.
                logging.warning("Respuesta de DiagNet rechazada: %s", error)
                datos_api = {
                    "inventario_encontrado": False,
                    "nombre_equipo": "",
                    "area": "",
                    "estado_equipo": "desconocido",
                    "latencia_ms": None,
                    "codigo_diagnostico": "IP_NOT_FOUND",
                }
            except Exception as error:
                logging.error("Error consultando DiagNet: %s", error)
                datos_api = {
                    "inventario_encontrado": False,
                    "nombre_equipo": "",
                    "area": "",
                    "estado_equipo": "desconocido",
                    "latencia_ms": None,
                    "codigo_diagnostico": "IP_NOT_FOUND",
                }

            inventario_encontrado = datos_api.get("inventario_encontrado")
            nombre_equipo = datos_api.get("nombre_equipo", "")
            area_equipo = datos_api.get("area", "")
            estado_equipo = datos_api.get("estado_equipo", "")
            latencia_ms = datos_api.get("latencia_ms")
            codigo_diagnostico = datos_api.get("codigo_diagnostico", "IP_NOT_FOUND")

            estado_ticket = "diagnosticado" if inventario_encontrado else "en_revision"

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            resultado_catalogo = self.consultar_catalogo_seguro(cursor, codigo_diagnostico)

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

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "success", "ticket": codigo_ticket}).encode("utf-8")
            )

        except Exception as e:
            # No se expone el detalle de la excepcion al cliente.
            logging.error("Error en crear_ticket: %s", e)
            self.send_response(500)
            self.end_headers()

    def consultar_diagnet(self, ip_reportada):
        """
        Consulta DiagNet por HTTPS, validando su certificado contra el
        certificado conocido del laboratorio (certificate pinning).

        Esto cierra la brecha de "suplantacion del servidor externo":
        si un atacante intenta hacerse pasar por DiagNet (por ejemplo
        mediante ARP Spoofing) sin poseer la clave privada real de
        diagnet.crt, la conexion TLS fallara antes de que TechNova
        procese ningun dato.
        """
        ip_codificada = quote(ip_reportada)
        url_diagnet = f"https://localhost:8080/diagnostico?ip={ip_codificada}"

        contexto_ssl = ssl.create_default_context()
        contexto_ssl.load_verify_locations(cafile="../../certs/diagnet.crt")

        with urllib.request.urlopen(url_diagnet, context=contexto_ssl, timeout=5) as response:
            respuesta_api = response.read().decode("utf-8")
            datos_api = json.loads(respuesta_api)

        return datos_api

    def consultar_catalogo_seguro(self, cursor, codigo_diagnostico):
        """
        Busca el codigo de diagnostico en el catalogo interno usando
        una consulta parametrizada (Prepared Statement).

        A diferencia de la version vulnerable, aqui NUNCA se concatena
        codigo_diagnostico dentro del texto SQL: el motor de base de
        datos siempre lo trata como un valor literal, nunca como
        parte de la sintaxis de la consulta.
        """
        cursor.execute(
            """
            SELECT
                descripcion,
                nivel_alerta,
                recomendacion
            FROM catalogo_diagnosticos
            WHERE codigo = %s;
            """,
            (codigo_diagnostico,),
        )
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
            # No se envia "detalle" al cliente (a diferencia de la
            # version vulnerable); solo se registra en el log interno.
            logging.error("Error consultando tickets: %s", error)
            self.responder_json(
                {
                    "status": "error",
                    "mensaje": "Error consultando tickets",
                },
                status=500,
            )

    def consultar_ticket(self):
        """
        Consulta pública de seguimiento de ticket.

        Contramedida aplicada:
        ya no se consulta el ticket solo por un identificador predecible.
        Se exige también el correo del solicitante para reducir el riesgo
        de enumeración de tickets.Además, la respuesta
        pública no expone datos técnicos internos como IP reportada,
        código diagnóstico o mensaje diagnóstico completo.
        """
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("codigo_ticket", "").strip().upper()
            correo_solicitante = params.get("correo_solicitante", "").strip().lower()

            if not codigo_ticket or not correo_solicitante:
                self.responder_json(
                    {
                        "status": "error",
                        "message": "Debe ingresar el código del ticket y el correo del solicitante."
                    },
                    status=400,
                )
                return

            if not codigo_ticket.startswith("TK-") or len(codigo_ticket) != 9 or not codigo_ticket[3:].isdigit():
                self.responder_json(
                    {
                        "status": "error",
                        "message": "El formato del código de ticket no es válido."
                    },
                    status=400,
                )
                return

            if "@" not in correo_solicitante or "." not in correo_solicitante:
                self.responder_json(
                    {
                        "status": "error",
                        "message": "El correo ingresado no tiene un formato válido."
                    },
                    status=400,
                )
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()
            # La consulta usa código + correo para verificar propiedad básica del ticket.
            # También se usan parámetros para evitar inyección SQL en la consulta pública.
            cursor.execute(
                """
                SELECT
                    codigo_ticket,
                    estado,
                    empresa_solicitante,
                    creado_en
                FROM tickets
                WHERE codigo_ticket = %s
                  AND LOWER(correo_solicitante) = %s;
                """,
                (codigo_ticket, correo_solicitante),
            )

            fila = cursor.fetchone()

            cursor.close()
            conexion.close()

            if fila is None:
                self.responder_json(
                    {
                        "status": "error",
                        "message": "No se encontró un ticket con los datos ingresados."
                    },
                    status=404,
                )
                return

            estado = fila[1]

            mensajes_estado = {
                "diagnosticado": "El incidente fue revisado automáticamente y no se detectaron fallas técnicas en el equipo reportado.",
                "en_revision": "El incidente está siendo revisado por el equipo de soporte Nivel 1.",
                "asignado": "El incidente fue revisado por soporte y asignado a un área especializada para su atención.",
                "cerrado": "El incidente fue solucionado y el ticket fue cerrado correctamente.",
            }

            ticket = {
                "codigo_ticket": fila[0],
                "estado": estado,
                "empresa_solicitante": fila[2],
                "creado_en": str(fila[3]),
                "mensaje_estado": mensajes_estado.get(
                    estado, "El caso se encuentra registrado en el sistema."
                ),
            }

            self.responder_json({"status": "success", "ticket": ticket})

        except Exception as error:
            logging.error("Error consultando ticket: %s", error)

            self.responder_json(
                {
                    "status": "error",
                    "message": "No se pudo consultar el ticket en este momento.",
                },
                status=500,
            )

    def login(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")

            params = json.loads(post_data)
            usuario = params.get("usuario", "").strip()
            password = params.get("password", "").strip()

            MENSAJE_GENERICO = "Usuario o contraseña incorrectos."

            if not usuario or not password:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Datos Incompletos"}).encode("utf-8"))
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # Se obtiene el hash bcrypt almacenado; la verificacion de la
            # contraseña se hace en Python con bcrypt.checkpw, NUNCA
            # comparando hashes dentro del SQL (como hacia MD5(%s) en la
            # version vulnerable).
            cursor.execute(
                "SELECT id, nombre, tipo_empleado, password_hash FROM empleados WHERE usuario = %s AND activo = TRUE",
                (usuario,),
            )
            fila = cursor.fetchone()
            cursor.close()
            conexion.close()

            login_valido = None

            if fila is not None:
                empleado_id, nombre, tipo_empleado, password_hash = fila
                if bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                    login_valido = (empleado_id, nombre, tipo_empleado)

            # Mensaje de error identico exista o no el usuario, para
            # evitar que un atacante pueda enumerar usuarios validos
            # observando la diferencia entre "usuario no autorizado" y
            # "contraseña invalida" (como si ocurria en la version
            # vulnerable).
            if login_valido is None:
                respuesta = {"status": "error", "message": MENSAJE_GENERICO}
            else:
                respuesta = {"status": "success"}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")

            if login_valido:
                empleado_id = login_valido[0]
                self.send_header("Set-Cookie", f"empleado_id={empleado_id}; Path=/; HttpOnly; Secure")

            self.end_headers()
            self.wfile.write(json.dumps(respuesta).encode("utf-8"))

        except Exception as e:
            logging.error("Error en login: %s", e)
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": "Servidor No Disponible. Intente más tarde."}).encode("utf-8"))

    def cambiar_estado(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id")
            nuevo_estado = params.get("nuevo_estado")

            ESTADOS_VALIDOS = {"abierto", "en_revision", "diagnosticado", "asignado", "cerrado"}

            if codigo_ticket and nuevo_estado in ESTADOS_VALIDOS:
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
            logging.error("Error cambiando estado: %s", e)
            self.responder_json({"status": "error"}, status=500)

    def asignar_ticket(self):
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id")
            analista_correo = params.get("analista")
            mensaje = params.get("mensaje")

            logging.info(
                "Simulacion de correo enviado a %s para ticket %s: %s",
                analista_correo, codigo_ticket, mensaje,
            )

            if codigo_ticket:
                conexion = obtener_conexion()
                cursor = conexion.cursor()
                cursor.execute(
                    "UPDATE tickets SET estado = 'asignado', actualizado_en = CURRENT_TIMESTAMP WHERE codigo_ticket = %s",
                    (codigo_ticket,)
                )
                conexion.commit()
                cursor.close()
                conexion.close()

            self.responder_json({"status": "ok"})
        except Exception as e:
            logging.error("Error asignando ticket: %s", e)
            self.responder_json({"status": "error"}, status=500)

    def obtener_empleado_sesion(self):
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

        except Exception as error:
            logging.error("Error obteniendo sesion: %s", error)
            return None

    def empleado_actual(self):
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
        self.send_response(302)
        self.send_header("Location", "/login.html")
        self.send_header("Set-Cookie", "empleado_id=; Path=/; Max-Age=0")
        self.end_headers()


if __name__ == "__main__":
    servidor = HTTPServer(("localhost", 3000), TechNovaHandler)

    contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto_ssl.load_cert_chain(
        certfile="../../certs/technova.crt",
        keyfile="../../certs/technova.key",
    )
    servidor.socket = contexto_ssl.wrap_socket(servidor.socket, server_side=True)

    print("TechNova App (segura) corriendo en https://localhost:3000")
    print("Debe estar activa la API DiagNet en https://localhost:8080")
    print("Si no existen los certificados, ejecute antes: bash certs/generar_certs.sh")
    servidor.serve_forever()
