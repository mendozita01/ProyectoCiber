# TechNova IT Services – Laboratorio de Ciberseguridad

Proyecto académico de simulación ofensiva y defensiva sobre un portal de soporte técnico llamado **TechNova**, conectado a un servicio externo de diagnóstico llamado **DiagNet**.  
El objetivo del laboratorio es demostrar cómo una cadena de ataque puede iniciar con reconocimiento de servicios, abuso de una consulta pública de tickets, manipulación de una respuesta de API, SQL Injection indirecta y recuperación de credenciales; y posteriormente evidenciar cómo la versión asegurada corta esa cadena mediante controles defensivos.

> **Uso permitido:** este proyecto está diseñado únicamente para un entorno académico, controlado y autorizado. No debe utilizarse contra sistemas reales ni redes de terceros.

---

## 1. Descripción general del escenario

El laboratorio simula una empresa que recibe incidencias técnicas mediante un portal web. Cuando un usuario crea un ticket, TechNova consulta a DiagNet para diagnosticar la IP reportada. La respuesta de DiagNet contiene un `codigo_diagnostico`, que luego TechNova utiliza para consultar su catálogo interno de diagnósticos.

El proyecto contempla dos enfoques:

- **Versión vulnerable:** construida intencionalmente con debilidades para demostrar el ataque.
- **Versión asegurada:** corregida con controles de comunicación segura, validación de datos, consultas parametrizadas, protección de credenciales, tickets no predecibles y trazabilidad mediante logs.

---

## 2. Objetivos del proyecto

- Implementar un laboratorio controlado con máquinas virtuales.
- Simular una cadena de ataque contra una aplicación web interna.
- Demostrar riesgos asociados a:
  - Consumo no seguro de APIs.
  - SQL Injection indirecta.
  - Exposición de información mediante tickets.
  - Fallas criptográficas por uso de MD5.
- Implementar medidas correctivas en la versión asegurada.
- Evidenciar la ineficacia del ataque tras la remediación.

---

## 3. Arquitectura del laboratorio

| Máquina | Rol | IP usada en la defensa | Función |
|---|---|---:|---|
| Kali Linux | Red Team | `192.168.0.3` | Reconocimiento, captura de tráfico, validación ofensiva y pruebas con herramientas. |
| Ubuntu TechNova | Blue Team / Víctima | `192.168.0.4` | Portal web, backend de TechNova, panel administrativo y conexión a PostgreSQL. |
| Ubuntu DiagNet | Servicio externo | `192.168.0.5` | API de diagnóstico consultada por TechNova. |

Las máquinas trabajan dentro de una red NAT controlada en VirtualBox. Las IP pueden variar si no están fijadas manualmente, por lo que deben verificarse antes de ejecutar las pruebas.

---

## 4. Componentes del sistema

### 4.1 TechNova

TechNova es el portal principal del laboratorio. Incluye:

- Página pública de soporte.
- Creación de tickets.
- Consulta pública de seguimiento.
- Backend para consultar DiagNet.
- Panel administrativo para empleados.
- Registro de eventos en `technova_seguro.log`.

### 4.2 DiagNet

DiagNet es el servicio externo de diagnóstico. Su función es recibir una IP, validar si pertenece al inventario y devolver un diagnóstico técnico en formato JSON.

### 4.3 PostgreSQL

PostgreSQL almacena la información del sistema, incluyendo:

- Empleados.
- Tickets.
- Catálogo de diagnósticos.
- Inventario de IPs monitoreadas.
- Eventos o datos auxiliares del laboratorio.

---

## 5. Tecnologías utilizadas

### Infraestructura

- VirtualBox.
- Kali Linux.
- Ubuntu Desktop para TechNova y DiagNet.
- Red NAT controlada para las máquinas virtuales.

### Backend y aplicación

- Python 3.
- Librerías estándar de Python:
  - `http.server`
  - `ssl`
  - `json`
  - `urllib`
  - `hashlib`
  - `hmac`
  - `secrets`
  - `logging`
  - `ipaddress`
- PostgreSQL.
- Extensión `pgcrypto` de PostgreSQL para generación segura de valores aleatorios.

### Dependencias externas recomendadas

Según el entorno, el proyecto puede requerir:

```bash
python -m pip install psycopg2-binary python-dotenv
```

Si el repositorio incluye `requirements.txt`, usar preferiblemente:

```bash
python -m pip install -r requirements.txt
```

### Herramientas de evaluación y validación

- Nmap.
- curl.
- Wireshark.
- Bettercap.
- iptables.
- mitmproxy.
- John the Ripper.
- pgAdmin o psql.
- Visual Studio Code.

---

## 6. Configuración de base de datos

Crear una base de datos en PostgreSQL. El nombre puede variar según el archivo `.env`, por ejemplo:

```text
technova
```

o

```text
technova_db
```

Luego ejecutar los scripts en este orden:

```sql
create.sql
insert.sql
```

Con `psql`, un ejemplo sería:

```bash
psql -U postgres -d technova -f database/create.sql
psql -U postgres -d technova -f database/insert.sql
```

También puede hacerse desde pgAdmin abriendo y ejecutando los archivos SQL manualmente.

---

## 7. Variables de entorno

Crear un archivo `.env` en la raíz del proyecto o en la carpeta indicada por el backend, tomando como base `.env.example`.

Ejemplo orientativo:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=technova
DB_USER=postgres
DB_PASSWORD=tu_password

TECHNOVA_HOST=0.0.0.0
TECHNOVA_PORT=3000

DIAGNET_HOST=0.0.0.0
DIAGNET_PORT=8080
DIAGNET_URL=https://192.168.0.5:8080

DIAGNET_CERT=../../certs/diagnet.crt
TECHNOVA_CERT=../../certs/technova.crt
TECHNOVA_KEY=../../certs/technova.key
```

Ajustar los valores según la IP real de las máquinas virtuales.

---

## 8. Instalación del entorno

### 8.1 Clonar el repositorio

```bash
git clone https://github.com/mendozita01/ProyectoCiber.git
cd ProyectoCiber
```

### 8.2 Crear entorno virtual

En Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 8.3 Instalar dependencias

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si no existe `requirements.txt`, instalar manualmente las dependencias usadas por el backend:

```bash
python -m pip install psycopg2-binary python-dotenv
```

---

## 9. Certificados para la versión asegurada

La versión asegurada utiliza certificados para proteger la comunicación entre TechNova y DiagNet.

Si se necesita regenerarlos:

```bash
cd certs
bash generar_certs.sh
```

Los certificados del laboratorio son de uso académico y local. No deben reutilizarse en producción.

---

## 10. Ejecución de DiagNet

Desde la raíz del proyecto:

```bash
cd diagnet_api
python servidor_api.py
```

DiagNet debe quedar disponible en el puerto `8080`.

Ejemplo de acceso en el laboratorio:

```text
https://192.168.0.5:8080/diagnostico?ip=<IP_DEL_INVENTARIO>
```

---

## 11. Ejecución de TechNova

En otra terminal:

```bash
cd technova_app/backend
python app.py
```

TechNova debe quedar disponible en el puerto `3000`.

Ejemplo de acceso:

```text
https://192.168.0.4:3000
```

En el equipo local también puede usarse:

```text
https://localhost:3000
```

Dependiendo del navegador, puede aparecer una advertencia por certificado autofirmado. Esto es normal en el laboratorio.

---

## 12. Funcionalidades principales

### Portal público

- Crear ticket de soporte.
- Consultar seguimiento de ticket.
- Validación de IP reportada contra inventario.
- Respuesta pública con información mínima.

### Consulta de tickets asegurada

La versión asegurada corrige la exposición de información mediante:

- Códigos de ticket no secuenciales.
- Validación de formato del código.
- Consulta por código de ticket y correo del solicitante.
- Minimización de información en la respuesta pública.

### Panel administrativo

- Inicio de sesión de empleados.
- Visualización de tickets.
- Cambio de estado.
- Asignación o escalamiento de incidentes.
- Cierre de sesión.

### Estados de ticket

| Estado | Significado |
|---|---|
| `diagnosticado` | DiagNet revisó la IP y no encontró fallas. |
| `en_revision` | DiagNet detectó un problema técnico o el caso requiere revisión. |
| `asignado` | Soporte Nivel 1 escaló o asignó el incidente. |
| `cerrado` | El problema fue solucionado y el ticket quedó archivado. |

---

## 13. Riesgos demostrados en la versión vulnerable

### ID-1: Consumo no seguro de APIs

TechNova consumía la respuesta de DiagNet sin validar suficientemente su contenido ni proteger adecuadamente la comunicación. Esto permitía manipular el campo `codigo_diagnostico`.

### SQL Injection indirecta tipo UNION / In-band

La inyección no ocurría directamente desde un formulario, sino a través del dato manipulado recibido desde DiagNet. El valor `codigo_diagnostico` terminaba siendo usado en una consulta SQL vulnerable.

### Exposición de información mediante tickets

La consulta pública de tickets permitía obtener información útil para continuar la cadena de ataque, como datos técnicos o IPs reportadas.

### ID-2: Fallas criptográficas

Las contraseñas estaban almacenadas con MD5, un hash rápido, antiguo, sin salt individual y no adecuado para proteger contraseñas.

---

## 14. Medidas implementadas en la versión asegurada

### Comunicación protegida

- Uso de HTTPS entre TechNova y DiagNet.
- Certificado conocido de DiagNet.
- Rechazo de comunicaciones no confiables.
- Registro de errores de certificado en `technova_seguro.log`.

### Validación de respuesta de DiagNet

- Esquema esperado de respuesta.
- Validación de claves faltantes o sobrantes.
- Validación de tipos de datos.
- Lista blanca para `codigo_diagnostico`.

### Protección contra SQL Injection

- Eliminación de concatenación directa en consultas SQL.
- Uso de consultas parametrizadas.
- Tratamiento de `codigo_diagnostico` como dato, no como instrucción SQL.

### Tickets más seguros

- Uso de `pgcrypto`.
- Función `asignar_codigo_ticket_seguro`.
- Trigger para asignación automática de código.
- Códigos no secuenciales.
- Validación de formato de ticket.
- Consulta pública con código + correo.
- Respuesta pública mínima.

### Protección de contraseñas

- Reemplazo de MD5 por `PBKDF2-HMAC-SHA256`.
- Salt individual por usuario.
- `150000` iteraciones.
- Verificación mediante comparación de hash derivado.
- La contraseña no se descifra ni se almacena en texto claro.

### Trazabilidad

- Registro de eventos en `technova_seguro.log`.
- Errores de certificado.
- IPs no registradas.
- Fallos de autenticación.
- Errores o respuestas inválidas del servicio externo.

---

## 15. Validación defensiva esperada

Durante la defensa del proyecto se debe evidenciar que:

- Kali puede reconocer servicios, pero no avanzar igual que antes.
- La consulta pública de tickets ya no permite obtener fácilmente información técnica útil.
- La IP reportada se valida contra el inventario de DiagNet.
- Wireshark ya no muestra el JSON en texto plano entre TechNova y DiagNet.
- Los errores de certificado quedan registrados.
- La SQL Injection indirecta queda bloqueada por validación y consultas parametrizadas.
- Las contraseñas ya no se almacenan como MD5.
- John the Ripper no recupera contraseñas con el procedimiento usado en la versión vulnerable.

---

## 16. Enlace a máquinas virtuales configuradas

Máquinas virtuales usadas para la demostración:

```text
https://drive.google.com/file/d/1wd0_FrPQRb5Lxonssh68AB1sdkgYFjne/view?usp=sharing
```

---

