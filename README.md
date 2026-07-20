# TechNova IT Services — Versión Asegurada

Rama `version-asegurada` del proyecto de Ciberseguridad NRC 26999.
Contramedidas para **API10:2023 (Consumo No Seguro de APIs)** y
**A04:2025 (Fallas Criptográficas)**.

> El código de la versión vulnerable (con los comentarios explicando cada
> falla) vive en la rama `version-vulnerable` de este mismo repositorio.

## Stack tecnológico real

- **Backend:** Python 3 puro, usando `http.server` (sin frameworks) tanto
  para TechNova como para DiagNet.
- **Base de datos:** PostgreSQL (via `psycopg2`).
- **Frontend:** HTML/CSS/JS nativo (sin frameworks).
- **Cifrado de contraseñas:** `bcrypt` (factor de costo 12).
- **Transporte:** HTTPS/TLS con certificados autofirmados del laboratorio.

## Estructura del repositorio

```
ProyectoCiber/
├── certs/                     # Certificados TLS autofirmados (laboratorio)
│   └── generar_certs.sh
├── database/
│   ├── create.sql
│   └── insert.sql             # Usuarios de demo con hash bcrypt
├── diagnet_api/
│   ├── db.py
│   └── servidor_api.py        # API externa DiagNet (HTTPS)
├── technova_app/
│   ├── backend/
│   │   ├── app.py             # Backend TechNova (HTTPS + validaciones)
│   │   ├── db.py
│   │   └── generar_hash.py    # Utilidad para generar hashes bcrypt
│   └── frontend/
├── requirements.txt
└── .env.example
```

## Contramedidas aplicadas

### API10 — Consumo No Seguro de APIs

| Falla en la versión vulnerable | Contramedida en esta versión |
|---|---|
| El backend confiaba ciegamente en el JSON de DiagNet | `validar_respuesta_diagnet()` valida esquema completo (claves + tipos) antes de usar el dato |
| `codigo_diagnostico` se concatenaba directo en el SQL | Se usa `WHERE codigo = %s` (consulta parametrizada) |
| Sin lista blanca de valores permitidos | `CODIGOS_DIAGNOSTICO_VALIDOS` rechaza cualquier valor fuera de los 5 códigos reales del catálogo |
| Canal TechNova↔DiagNet en HTTP plano | Ambos servicios corren sobre HTTPS |
| No se verificaba la identidad de DiagNet | TechNova valida el certificado de DiagNet (`certificate pinning` contra `certs/diagnet.crt`); un servidor suplantado sin la clave privada real es rechazado por el handshake TLS |

### A04 — Fallas Criptográficas

| Falla en la versión vulnerable | Contramedida en esta versión |
|---|---|
| Contraseñas con `MD5()` sin salt | Hashes `bcrypt` (salt individual embebido, factor de costo 12) |
| Comparación de hash dentro del SQL (`password_hash = MD5(%s)`) | Verificación en Python con `bcrypt.checkpw()` |
| Login por HTTP plano | Formulario y API sirven por HTTPS |
| Mensajes distintos para "usuario no existe" vs "contraseña incorrecta" (permite enumerar usuarios) | Mensaje genérico único: "Usuario o contraseña incorrectos" |
| Errores SQL/excepciones expuestos al cliente (`"detalle": str(error)`) | Los detalles se registran solo en `technova_seguro.log`; el cliente recibe un mensaje genérico |

## Cómo desplegar y probar

### 1. Generar los certificados TLS del laboratorio (una sola vez)

```bash
bash certs/generar_certs.sh
```

### 2. Preparar la base de datos

```bash
createdb technova   # o el nombre que definas en .env
psql -d technova -f database/create.sql
psql -d technova -f database/insert.sql
cp .env.example .env   # y completar credenciales de PostgreSQL
```

### 3. Instalar dependencias de Python

```bash
pip install -r requirements.txt --break-system-packages
```

### 4. Levantar los servicios (en terminales separadas)

```bash
# Terminal 1 — API DiagNet
cd diagnet_api
python3 servidor_api.py
# -> https://localhost:8080

# Terminal 2 — App TechNova
cd technova_app/backend
python3 app.py
# -> https://localhost:3000
```

El navegador mostrará una advertencia de certificado no confiable (normal,
es autofirmado y solo para el laboratorio): aceptar la excepción para
continuar.

### 5. Usuarios de demo (login en `/login.html`)

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Admin123` | admin |
| `soporte1` | `Soporte123` | soporte |
| `analista1` | `Analista123` | analista |

## Prueba de cierre (validar que el ataque ya no funciona)

Repetir desde Kali el mismo ataque documentado en la rama
`version-vulnerable`:

1. Intentar interceptar/alterar el JSON de DiagNet en tránsito (MITM/ARP
   Spoofing): la conexión TLS entre TechNova y DiagNet debe romperse o
   TechNova debe rechazar el certificado si no corresponde al de
   `certs/diagnet.crt`.
2. Enviar un `codigo_diagnostico` manipulado (por ejemplo los payloads de
   `payloads.txt` de la rama vulnerable): `validar_respuesta_diagnet()`
   debe rechazarlo antes de que llegue a la consulta SQL — no debe
   aparecer ningún error de sintaxis SQL en la respuesta ni en pantalla.
3. Intentar extraer y crackear `password_hash` de la tabla `empleados`:
   aunque se obtenga la base de datos, los hashes son `bcrypt` con salt
   individual, por lo que un ataque de diccionario/Rainbow Table sobre
   ellos deja de ser viable en un tiempo razonable.

Capturar evidencia (pantallazos) de cada paso fallando como cierre del
proyecto.
