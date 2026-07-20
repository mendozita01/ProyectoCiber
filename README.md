## 🛠️ Instalación y Dependencias del Proyecto

Este apartado detalla el software, las herramientas y las librerías necesarias para construir, ejecutar y auditar el portal "TechNova". El entorno fue diseñado estratégicamente para permitir la creación manual de vulnerabilidades, cumpliendo con la restricción de no utilizar herramientas que automaticen la seguridad.

### 1. Infraestructura de Virtualización (Laboratorio)
Para llevar a cabo la simulación de ataque y defensa en un entorno controlado y seguro, el proyecto depende de:
* **VirtualBox:** Hipervisor utilizado para el despliegue y gestión de las máquinas virtuales.
* **Ubuntu Desktop 22.04 LTS (Blue Team):** Actuará como el servidor "Víctima" donde se desplegará el sistema en su fase final.
* **Kali Linux (Red Team):** Máquina preconfigurada con herramientas de seguridad ofensiva, utilizada para ejecutar los exploits, interceptar tráfico y realizar el criptoanálisis.

### 2. Entorno de Desarrollo Local
Herramientas instaladas en el equipo anfitrión para el desarrollo y prueba del código:
* **Visual Studio Code:** Editor de código fuente principal.
* **Python (v3.12+):** Lenguaje de programación core del backend. *(Nota: Es imperativo asegurar que el ejecutable esté agregado al `PATH` del sistema operativo durante su instalación).*
* **XAMPP:** Entorno que provee el motor de base de datos **MariaDB/MySQL**, necesario para almacenar la tabla de usuarios y simular el almacenamiento inseguro de credenciales.

### 3. Dependencias del Código (Librerías)
Dado que está prohibido el uso de frameworks robustos que mitiguen ataques por defecto, el sistema se construyó con las siguientes dependencias mínimas:
* **Flask (`flask`):** Micro-framework web para Python. Se seleccionó específicamente porque facilita el enrutamiento web pero **no incluye** mecanismos de seguridad nativos (como sanitización automática de inputs o bloqueo de inyecciones), lo que permite materializar manualmente el **Consumo Inseguro de APIs (Riesgo ID-1)**.
* **Hashlib (`hashlib`):** Librería nativa de Python (no requiere instalación vía `pip`). Se emplea para aplicar de forma deliberada el algoritmo **MD5** sin *salting* a las contraseñas de los usuarios, introduciendo la **Falla Criptográfica (Riesgo ID-2)** requerida por la rúbrica.

### 4. Maquinas virtuales configuradas 
https://drive.google.com/file/d/1wd0_FrPQRb5Lxonssh68AB1sdkgYFjne/view?usp=sharing   

### 5. Comandos de Instalación
Para replicar el entorno de ejecución en una terminal local, se deben seguir estos pasos:


```bash
# 1. Clonar el repositorio en el equipo local
git clone [https://github.com/mendozita01/ProyectoCiber.git](https://github.com/mendozita01/ProyectoCiber.git)

# 2. Acceder al directorio del proyecto clonado
cd ProyectoCiber

# 3. Crear en postgres una base de datos de nombre 
technova

# 4. Dentro de pgAdmin ejecutar los scripts 
create.sql 
insert.sql  

# 5. Crear el archivo .env en la raíz del proyecto, usando como base :
.env.example.

# 6. Crear el entorno virtual de Python
python -m venv .venv

# 7. Activar el entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Linux (Ubuntu Desktop - Blue Team):
# source .venv/bin/activate

# 8. Instalar las dependencias 
# Si el proyecto cuenta con un archivo requirements.txt:
python -m pip install -r requirements.txt
# En caso de instalarlas manualmente:
# python -m pip install flask

# 9. Abrir una terminal para DiagNet:
cd diagnet_api python servidor_api.py

# 10. Abrir otra terminal para TechNova
cd technova_app/backend python app.py

# 11. Abrir en el navegador
http://localhost:3000



