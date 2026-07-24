# TechNova IT Services — Versión Vulnerable

Rama `version-vulnerable` del proyecto de Ciberseguridad NRC 26999.  
Implementación intencionalmente vulnerable para demostrar la cadena ofensiva asociada a **API10:2023 (Consumo No Seguro de APIs)** y **A04:2025 (Fallas Criptográficas)**.

> La versión corregida del proyecto vive en la rama `version-asegurada` de este mismo repositorio.  
> Este código vulnerable es únicamente para fines académicos, dentro de un laboratorio controlado y autorizado.

## Stack tecnológico real

- **Backend:** Python 3 puro, usando `http.server` tanto para TechNova como para DiagNet.
- **Base de datos:** PostgreSQL (via `psycopg2`).
- **Frontend:** HTML/CSS/JS nativo (sin frameworks).
- **Hash de contraseñas:** MD5 sin salt individual, implementado de forma deliberadamente insegura para evidenciar la falla criptográfica.
- **Transporte:** HTTP plano entre TechNova y DiagNet, permitiendo observar y manipular respuestas durante la demostración ofensiva.

## Estructura del repositorio

```
ProyectoCiber/
├── database/
│   ├── create.sql
│   └── insert.sql             # Usuarios de demo con password_hash en MD5
├── diagnet_api/
│   ├── db.py
│   └── servidor_api.py        # API externa DiagNet vulnerable (HTTP)
├── technova_app/
│   ├── backend/
│   │   ├── app.py             # Backend TechNova vulnerable
│   │   └── db.py
│   └── frontend/
│       ├── index.html
│       ├── login.html
│       ├── admin.html
│       └── archivos estáticos
├── payloads.txt               # Payloads usados en la demostración controlada
├── requirements.txt
└── .env.example
```

## Vulnerabilidades implementadas

### API10 — Consumo No Seguro de APIs

| Comportamiento vulnerable | Riesgo demostrado |
|---|---|
| El backend confía directamente en el JSON recibido desde DiagNet | Un atacante puede alterar la respuesta externa y hacer que TechNova procese datos manipulados |
| `codigo_diagnostico` se usa sin validación estricta | Se acepta contenido inesperado dentro de un campo que debería tener valores controlados |
| No existe lista blanca de códigos permitidos | Valores fuera del catálogo pueden llegar al backend |
| Canal TechNova↔DiagNet en HTTP plano | La respuesta puede observarse en texto claro durante la comunicación |
| No se verifica la identidad de DiagNet | Un atacante en posición de intermediario puede intentar modificar la respuesta enviada a TechNova |

### SQL Injection indirecta tipo UNION / In-band

| Comportamiento vulnerable | Riesgo demostrado |
|---|---|
| `codigo_diagnostico` se concatena dentro de una consulta SQL | El dato externo puede convertirse en parte ejecutable de SQL |
| La inyección no entra directamente desde un formulario, sino desde la respuesta alterada de DiagNet | Se demuestra una SQL Injection indirecta |
| El resultado vuelve por el mismo flujo de la aplicación | Se clasifica como inyección dentro de banda, específicamente tipo UNION |
| La consulta permite consultar información interna de PostgreSQL | Se pueden enumerar tablas, columnas, usuarios, roles y hashes en el laboratorio |

### A04 — Fallas Criptográficas

| Comportamiento vulnerable | Riesgo demostrado |
|---|---|
| Contraseñas almacenadas con `MD5()` sin salt individual | Hashes rápidos y débiles para almacenar contraseñas |
| Usuarios con hashes de 32 caracteres en la tabla `empleados` | Facilita la identificación del formato MD5 durante el análisis |
| Uso de diccionarios contra hashes MD5 | Permite recuperar contraseñas de usuarios de prueba en el laboratorio |
| Login sobre HTTP plano | Las credenciales pueden quedar expuestas si el tráfico es observado |
| Mensajes o errores demasiado específicos | Pueden ayudar a la enumeración o análisis del comportamiento del sistema |

### Consulta pública de tickets

| Comportamiento vulnerable | Riesgo demostrado |
|---|---|
| Códigos de ticket secuenciales, como `TK-000001`, `TK-000002` | Enumeración de identificadores predecibles |
| Consulta pública basada únicamente en el código del ticket | Broken Access Control / IDOR |
| Respuesta pública con información técnica sensible | Exposición de datos útiles para continuar la cadena del ataque |
| Visualización de IP reportada o datos de diagnóstico | Permite obtener una IP válida para activar el flujo con DiagNet |

## Cómo desplegar y probar

### 1. Preparar la base de datos

```bash
createdb technova   # o el nombre que definas en .env
psql -d technova -f database/create.sql
psql -d technova -f database/insert.sql
cp .env.example .env   # y completar credenciales de PostgreSQL
```

También puede hacerse desde pgAdmin ejecutando primero `create.sql` y luego `insert.sql`.

### 2. Instalar dependencias de Python

```bash
pip install -r requirements.txt --break-system-packages
```

Si no existe `requirements.txt`, instalar manualmente las dependencias usadas por el backend:

```bash
python -m pip install psycopg2-binary python-dotenv
```

### 3. Levantar los servicios (en terminales separadas)

```bash
# Terminal 1 — API DiagNet vulnerable
cd diagnet_api
python3 servidor_api.py
# -> http://localhost:8080

# Terminal 2 — App TechNova vulnerable
cd technova_app/backend
python3 app.py
# -> http://localhost:3000
```

### 4. Abrir el portal

```text
http://localhost:3000
```

En el laboratorio con máquinas virtuales, usar la IP correspondiente de la máquina TechNova, por ejemplo:

```text
http://192.168.0.4:3000
```

## Usuarios de demo

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin12` | admin |
| `soporte1` | `soporte123` | soporte |
| `analista1` | `analista123` | analista |

> En esta rama vulnerable, las contraseñas de estos usuarios se almacenan con MD5 para demostrar la falla criptográfica durante la práctica controlada.

## Flujo ofensivo esperado en el laboratorio

La demostración ofensiva se realiza desde Kali Linux dentro de la red NAT controlada. El objetivo es recorrer la cadena del ataque de forma controlada, no afectar sistemas reales.

### 1. Reconocimiento de red

Identificar las máquinas activas y los servicios de TechNova y DiagNet.

Comandos útiles:

```bash
hostname -I
ip route
nmap -sn -n 192.168.0.0/24
nmap -n -sV -p 3000,8080 192.168.0.4 192.168.0.5
```

### 2. Consulta pública de tickets

Probar códigos de ticket secuenciales para encontrar tickets existentes.  
Esta fase demuestra enumeración de identificadores predecibles, Broken Access Control / IDOR y exposición de información técnica.

### 3. Obtención de una IP reportada

A partir de la consulta pública, obtener una IP válida registrada en el sistema.  
Esta IP se usa para activar el flujo normal de diagnóstico con DiagNet.

### 4. Creación de ticket con IP válida

Crear un nuevo ticket usando una IP reconocida por DiagNet.  
Al crear el ticket, TechNova consulta a la API externa para obtener el diagnóstico.

### 5. Interceptación y modificación de la respuesta HTTP

En la versión vulnerable, la comunicación TechNova↔DiagNet ocurre por HTTP plano.  
Durante la práctica se usan herramientas como:

- Bettercap.
- Wireshark.
- iptables.
- mitmproxy.

Estas herramientas permiten observar el tráfico y modificar manualmente la respuesta HTTP de DiagNet dentro del entorno controlado.

### 6. SQL Injection indirecta

El campo `codigo_diagnostico` modificado en la respuesta de DiagNet llega al backend de TechNova.  
Como el backend vulnerable concatena ese valor en SQL, se demuestra una SQL Injection indirecta de tipo UNION / In-band.

### 7. Extracción de información interna

Mediante la inyección, se evidencia la posibilidad de consultar información interna de PostgreSQL, como:

- Tablas.
- Columnas.
- Usuarios.
- Roles.
- Hashes de contraseñas.

### 8. Cracking de hashes

Los hashes MD5 recuperados pueden probarse con John the Ripper en el laboratorio.  
Esta fase demuestra por qué MD5 no es adecuado para almacenar contraseñas.

### 9. Acceso con credenciales recuperadas

Con credenciales recuperadas de usuarios de prueba, se demuestra acceso no autorizado al panel administrativo de TechNova.

## Comandos útiles para validación

### Identificar IP de la máquina

```bash
hostname -I
```

### Ver ruta de red

```bash
ip route
```

### Descubrir hosts activos

```bash
nmap -sn -n 192.168.0.0/24
```

### Verificar servicios relevantes

```bash
nmap -n -sV -p 3000,8080 192.168.0.4 192.168.0.5
```

### Probar DiagNet directamente

```bash
curl "http://192.168.0.5:8080/diagnostico?ip=<IP_DEL_INVENTARIO>"
```

### Probar TechNova

```bash
curl "http://192.168.0.4:3000"
```

## Evidencias esperadas de la versión vulnerable

Durante la defensa del proyecto se deben capturar pantallazos o grabación de:

- Reconocimiento de máquinas desde Kali.
- Servicios activos en los puertos `3000` y `8080`.
- Consulta pública de tickets secuenciales.
- Obtención de una IP reportada.
- Creación de ticket con IP válida.
- Tráfico HTTP visible entre TechNova y DiagNet.
- Modificación de respuesta con mitmproxy.
- Visualización del resultado manipulado en TechNova.
- Demostración de SQL Injection indirecta tipo UNION / In-band.
- Enumeración de tablas y columnas.
- Extracción de usuarios, roles y hashes.
- Cracking de hashes MD5 con John the Ripper.
- Login exitoso con credenciales recuperadas.

## Relación con la versión asegurada

La rama `version-asegurada` corrige las debilidades demostradas en esta rama mediante:

| Debilidad vulnerable | Corrección en `version-asegurada` |
|---|---|
| HTTP plano entre TechNova y DiagNet | HTTPS/TLS con certificados del laboratorio |
| Sin verificación de identidad de DiagNet | Verificación del certificado esperado de DiagNet |
| JSON externo confiado automáticamente | Validación estricta de esquema, tipos y claves |
| Sin lista blanca de `codigo_diagnostico` | Lista blanca de códigos permitidos |
| SQL construido por concatenación | Consulta parametrizada |
| Tickets secuenciales | Códigos no secuenciales con `pgcrypto` |
| Consulta pública solo por código | Consulta por código + correo |
| Respuesta pública con datos técnicos | Respuesta pública mínima |
| MD5 sin salt | PBKDF2-HMAC-SHA256 con salt individual y 150 000 iteraciones |
| Errores visibles al cliente | Mensajes genéricos y trazabilidad en logs |

## Enlace a máquinas virtuales configuradas

Máquinas virtuales usadas para la demostración:

```text
https://drive.google.com/file/d/1wd0_FrPQRb5Lxonssh68AB1sdkgYFjne/view?usp=sharing
```

## Notas importantes

- Este proyecto es exclusivamente académico.
- La rama vulnerable contiene fallas implementadas de forma intencional.
- No debe ejecutarse fuera del laboratorio autorizado.
- No debe usarse contra redes, aplicaciones o servicios de terceros.
- Los usuarios, contraseñas, hashes, certificados e IPs son datos de práctica.
- Las IPs pueden cambiar si no están fijadas manualmente en la red NAT.
- Si los puertos `3000` o `8080` aparecen ocupados, se debe cerrar el proceso anterior o ajustar el puerto en la configuración.


