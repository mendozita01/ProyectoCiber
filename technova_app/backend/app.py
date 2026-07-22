import logging
import ssl
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import quote
import urllib.request
import json

import hashlib
import hmac
import secrets

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
#    - Las contrasenas se verifican con PBKDF2-HMAC-SHA256,
#      usando salt individual e iteraciones, no con MD5 sin salt.
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

# =========================================================
# HASH SEGURO DE CONTRASEÑAS - A04 Fallas Criptográficas
# =========================================================
# En la versión vulnerable se usaba MD5, un hash rápido y sin salt.
# En la versión asegurada se usa PBKDF2-HMAC-SHA256 con salt único
# e iteraciones para aumentar el costo de ataques de diccionario.
ITERACIONES_HASH = 150000


def generar_hash_password(password):
    """
    Genera un hash de contraseña usando PBKDF2-HMAC-SHA256.

    Formato almacenado:
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


def verificar_password(password, password_hash_guardado):
    """
    Verifica una contraseña comparando el hash calculado
    con el hash almacenado en la base de datos.

    No se desencripta la contraseña: se vuelve a calcular el hash
    usando el mismo salt y las mismas iteraciones.
    """
    try:
        algoritmo, iteraciones, salt, hash_guardado = password_hash_guardado.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iteraciones)
        )

        hash_calculado = hash_bytes.hex()

        return hmac.compare_digest(hash_calculado, hash_guardado)

    except Exception:
        return False

def validar_formato_codigo_ticket(codigo_ticket):
    """
    Valida el formato del código de ticket generado por PostgreSQL.

    Formato esperado:
    TK-XXXXXXXX

    Donde X puede ser una letra o número permitido.
    """
    caracteres_validos = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    if not isinstance(codigo_ticket, str):
        return False

    if not codigo_ticket.startswith("TK-"):
        return False

    if len(codigo_ticket) != 11:
        return False

    return all(caracter in caracteres_validos for caracter in codigo_ticket[3:])

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
    2. Contenga exactamente las claves esperadas, sin claves faltantes ni sobrantes.
    3. Tenga tipos de datos correctos.
    4. Tenga un codigo_diagnostico dentro de la lista blanca.

    Esta es la contramedida central para API10: en la version
    vulnerable, este objeto se usaba "tal cual" sin ninguna de
    estas verificaciones.
    """
    if not isinstance(datos, dict):
        raise RespuestaDiagNetInvalida("La respuesta de DiagNet no es un objeto JSON valido.")

    claves_esperadas = set(ESQUEMA_DIAGNET.keys())
    claves_recibidas = set(datos.keys())

    if claves_recibidas != claves_esperadas:
        claves_faltantes = claves_esperadas - claves_recibidas
        claves_sobrantes = claves_recibidas - claves_esperadas

        raise RespuestaDiagNetInvalida(
            f"La respuesta de DiagNet no cumple el esquema esperado. "
            f"Faltantes: {claves_faltantes}. Sobrantes: {claves_sobrantes}."
        )

    for clave, tipos_aceptados in ESQUEMA_DIAGNET.items():
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
        """
        Crea un ticket a partir de la incidencia reportada por el solicitante.

        En la versión asegurada, la respuesta de DiagNet no se usa directamente:
        primero se consulta por HTTPS, luego se valida su estructura y finalmente
        se consulta el catálogo interno mediante una consulta parametrizada.
        """
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            ip_reportada = params.get("ip_reportada", "").strip()

            if not ip_reportada:
                self.responder_json(
                    {
                        "status": "error",
                        "message": "Debe ingresar una IP para reportar el incidente."
                    },
                    status=400,
                )
                return

            nombre = params.get("nombre_solicitante", "Anónimo")
            correo = params.get("correo_solicitante", "sin@correo.com")
            telefono = params.get("telefono_solicitante", "")
            empresa = params.get("empresa_solicitante", "")
            descripcion = params.get("descripcion_problema", "")

            # 1. Consultar API externa de forma segura.
            # Antes, TechNova consumía la respuesta de DiagNet sin validar
            # si realmente venía del servicio esperado ni si el JSON era confiable.
            #
            # Ahora la consulta se realiza por HTTPS y consultar_diagnet()
            # valida el certificado conocido de DiagNet. Luego se valida
            # el esquema y la lista blanca de códigos diagnósticos.
            try:
                datos_api = self.consultar_diagnet(ip_reportada)
                datos_api = validar_respuesta_diagnet(datos_api)

            except RespuestaDiagNetInvalida as error:
                # Si la API devuelve una respuesta alterada, incompleta o con un
                # codigo_diagnostico fuera de la lista blanca, se rechaza.
                # El detalle queda en el log, pero no se muestra al usuario.
                logging.warning("Respuesta de DiagNet rechazada: %s", error)

                self.responder_json(
                    {
                        "status": "error",
                        "message": "No se pudo validar la respuesta del servicio de diagnóstico."
                    },
                    status=502,
                )
                return

            except Exception as error:
                # Error de comunicación, certificado, timeout o respuesta no válida.
                # En la versión asegurada no se continúa creando tickets con datos
                # inventados cuando la API externa no puede verificarse.
                logging.error("Error consultando DiagNet: %s", error)

                self.responder_json(
                    {
                        "status": "error",
                        "message": "No se pudo consultar el servicio de diagnóstico en este momento."
                    },
                    status=503,
                )
                return

            inventario_encontrado = datos_api.get("inventario_encontrado")
            nombre_equipo = datos_api.get("nombre_equipo", "")
            area_equipo = datos_api.get("area", "")
            estado_equipo = datos_api.get("estado_equipo", "")
            latencia_ms = datos_api.get("latencia_ms")
            codigo_diagnostico = datos_api.get("codigo_diagnostico", "")

            if not inventario_encontrado:
                logging.warning("IP no registrada en inventario DiagNet: %s", ip_reportada)

                self.responder_json(
                    {
                        "status": "error",
                        "message": "La IP reportada no se encuentra registrada."
                    },
                    status=404,
                )
                return

            # 2. Determinar el estado inicial según el código diagnóstico validado.
            if codigo_diagnostico == "OK-200":
                estado_ticket = "diagnosticado"
            else:
                estado_ticket = "en_revision"

            conexion = obtener_conexion()
            cursor = conexion.cursor()

            # 3. Consultar catálogo interno de forma segura.
            # codigo_diagnostico proviene de una API externa, por eso no se concatena
            # dentro del SQL. consultar_catalogo_seguro() usa parámetros (%s),
            # evitando que el valor recibido sea interpretado como sintaxis SQL.
            resultado_catalogo = self.consultar_catalogo_seguro(cursor, codigo_diagnostico)

            # 4. Guardar ticket.
            # El código público del ticket no se genera de forma secuencial en Python.
            # PostgreSQL lo asigna mediante trigger y guardar_ticket() lo recupera
            # con RETURNING codigo_ticket.
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

            self.responder_json(
                {
                    "status": "success",
                    "ticket": codigo_ticket,
                },
                status=200,
            )

        except Exception as e:
            # No se expone el detalle técnico al cliente.
            logging.error("Error en crear_ticket: %s", e)

            self.responder_json(
                {
                    "status": "error",
                    "message": "No se pudo crear el ticket en este momento."
                },
                status=500,
            )

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
        url_diagnet = f"https://0.0.0.0:8080/diagnostico?ip={ip_codificada}"

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
        empleado = self.validar_acceso_interno({"admin", "soporte", "analista"})

        if empleado is None:
            return

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
            logging.error("Error consultando tickets: %s", error)
            self.responder_json(
                {"status": "error", "mensaje": "Error consultando tickets"},
                status=500,
            )


    def validar_acceso_interno(self, roles_permitidos=None):
        """
        Valida que la ruta sea usada por un empleado autenticado y autorizado.
        """
        empleado = self.obtener_empleado_sesion()

        if empleado is None:
            self.responder_json(
                {"status": "error", "mensaje": "Debe iniciar sesión para acceder a este recurso."},
                status=401,
            )
            return None

        if roles_permitidos is not None and empleado["tipo_empleado"] not in roles_permitidos:
            self.responder_json(
                {"status": "error", "mensaje": "No tiene permisos para realizar esta acción."},
                status=403,
            )
            return None

        return empleado

    def consultar_ticket(self):
        """Consulta pública de seguimiento de ticket."""
        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("codigo_ticket", "").strip().upper()
            correo_solicitante = params.get("correo_solicitante", "").strip().lower()

            if not codigo_ticket or not correo_solicitante:
                self.responder_json(
                    {"status": "error", "message": "Debe ingresar el código del ticket y el correo del solicitante."},
                    status=400,
                )
                return

            if not validar_formato_codigo_ticket(codigo_ticket):
                self.responder_json(
                    {"status": "error", "message": "El formato del código de ticket no es válido."},
                    status=400,
                )
                return

            if "@" not in correo_solicitante or "." not in correo_solicitante:
                self.responder_json(
                    {"status": "error", "message": "El correo ingresado no tiene un formato válido."},
                    status=400,
                )
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute(
                """
                SELECT codigo_ticket, estado, empresa_solicitante, creado_en
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
                    {"status": "error", "message": "No se encontró un ticket con los datos ingresados."},
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
                "mensaje_estado": mensajes_estado.get(estado, "El caso se encuentra registrado en el sistema."),
            }

            self.responder_json({"status": "success", "ticket": ticket})

        except Exception as error:
            logging.error("Error consultando ticket: %s", error)
            self.responder_json(
                {"status": "error", "message": "No se pudo consultar el ticket en este momento."},
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
                if verificar_password(password, password_hash):
                    login_valido = (empleado_id, nombre, tipo_empleado)

            if login_valido is None:
                logging.warning("Intento de login fallido para usuario: %s", usuario)
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
        """Cambio interno de estado del ticket."""
        empleado = self.validar_acceso_interno({"admin", "soporte", "analista"})
        if empleado is None:
            return

        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id", "").strip().upper()
            nuevo_estado = params.get("nuevo_estado", "").strip()
            ESTADOS_VALIDOS = {"diagnosticado", "en_revision", "asignado", "cerrado"}

            if not validar_formato_codigo_ticket(codigo_ticket):
                self.responder_json({"status": "error", "mensaje": "El código del ticket no tiene un formato válido."}, status=400)
                return

            if nuevo_estado not in ESTADOS_VALIDOS:
                self.responder_json({"status": "error", "mensaje": "El estado indicado no es válido."}, status=400)
                return

            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute(
                """
                UPDATE tickets
                SET estado = %s,
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE codigo_ticket = %s;
                """,
                (nuevo_estado, codigo_ticket),
            )

            conexion.commit()
            cursor.close()
            conexion.close()
            self.responder_json({"status": "ok"})

        except Exception as error:
            logging.error("Error cambiando estado: %s", error)
            self.responder_json({"status": "error", "mensaje": "No se pudo cambiar el estado del ticket."}, status=500)

    def asignar_ticket(self):
        """Escalamiento interno de ticket."""
        empleado = self.validar_acceso_interno({"admin", "soporte"})
        if empleado is None:
            return

        try:
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = json.loads(post_data)

            codigo_ticket = params.get("ticket_id", "").strip().upper()
            analista_correo = params.get("analista", "").strip().lower()
            mensaje = params.get("mensaje", "").strip()

            if not validar_formato_codigo_ticket(codigo_ticket):
                self.responder_json({"status": "error", "mensaje": "El código del ticket no tiene un formato válido."}, status=400)
                return

            if "@" not in analista_correo or "." not in analista_correo:
                self.responder_json({"status": "error", "mensaje": "Debe ingresar un correo válido para el analista."}, status=400)
                return

            if not mensaje:
                self.responder_json({"status": "error", "mensaje": "Debe ingresar un mensaje para el escalamiento."}, status=400)
                return

            logging.info(
                "Escalamiento realizado por empleado %s para ticket %s hacia %s: %s",
                empleado["usuario"],
                codigo_ticket,
                analista_correo,
                mensaje,
            )

            conexion = obtener_conexion()
            cursor = conexion.cursor()
            cursor.execute(
                """
                UPDATE tickets
                SET estado = 'asignado',
                    actualizado_en = CURRENT_TIMESTAMP
                WHERE codigo_ticket = %s;
                """,
                (codigo_ticket,),
            )

            conexion.commit()
            cursor.close()
            conexion.close()
            self.responder_json({"status": "ok"})

        except Exception as error:
            logging.error("Error asignando ticket: %s", error)
            self.responder_json({"status": "error", "mensaje": "No se pudo asignar el ticket."}, status=500)

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
            self.responder_json({"status": "error", "mensaje": "No Hay Empleado Con Sesión Activa"}, status=401)
            return
        self.responder_json({"status": "ok", "empleado": empleado})

    def logout(self):
        self.send_response(302)
        self.send_header("Location", "/login.html")
        self.send_header("Set-Cookie", "empleado_id=; Path=/; Max-Age=0")
        self.end_headers()


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", 3000), TechNovaHandler)

    contexto_ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contexto_ssl.load_cert_chain(
        certfile="../../certs/technova.crt",
        keyfile="../../certs/technova.key",
    )
    servidor.socket = contexto_ssl.wrap_socket(servidor.socket, server_side=True)

    print("TechNova App (segura) corriendo en https://0.0.0.0:3000")
    print("Debe estar activa la API DiagNet en https://0.0.0.0:8080")
    print("Si no existen los certificados, ejecute antes: bash certs/generar_certs.sh")
    servidor.serve_forever()
