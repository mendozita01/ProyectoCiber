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
                with urllib.request.urlopen('http://192.168.0.5/api/diagnostico') as response:
                    api_data = json.loads(response.read().decode())
                    codigo = api_data['codigo_diagnostico']

                cursor = db.cursor()
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