from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request, json
import psycopg2
from urllib.parse import parse_qs

db = psycopg2.connect(
    host="localhost",
    port="5433", 
    user="postgres",
    password="1234", 
    dbname="technova_db"
)

class TechNovaHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="../frontend", **kwargs)

    def do_POST(self):
        if self.path == '/crear_ticket':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            ip_reportada = params.get('ip_reportada', [''])[0]

            try:
                # 1. Preparar el JSON que le vamos a enviar a la API DiagNet
                datos_para_api = json.dumps({"ip": ip_reportada}).encode('utf-8')
                
                # 2. Configurar la petición POST hacia la API 
                solicitud_api = urllib.request.Request(
                    'http://localhost:8080/diagnostico', 
                    data=datos_para_api, 
                    method='POST',
                    headers={'Content-Type': 'application/json'}
                )

                # 3. Hacer la llamada a la API y leer la respuesta
                with urllib.request.urlopen(solicitud_api) as response:
                    api_data = json.loads(response.read().decode('utf-8'))
                    # Extraer el código de la respuesta
                    codigo = api_data.get('codigo_diagnostico', 'ERROR_API')

                cursor = db.cursor()
                # VULNERABILIDAD: Concatenación directa (Inyección SQL)
                query = f"INSERT INTO tickets (ip_reportada, codigo_diagnostico) VALUES ('{ip_reportada}', '{codigo}')"
                cursor.execute(query)
                db.commit()
                
                self.send_response(200)
                self.end_headers()
                self.wfile.write(f"<h1>Ticket creado. Código: {codigo}</h1>".encode())
            
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())

server = HTTPServer(('0.0.0.0', 3000), TechNovaHandler)
print("TechNova App (Python) corriendo en puerto 3000")
server.serve_forever()