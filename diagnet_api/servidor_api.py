from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/diagnostico':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "codigo_diagnostico": "DIAG-550"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

server = HTTPServer(('0.0.0.0', 80), APIHandler)
print("DiagNet API corriendo en puerto 80 (Nativo)")
server.serve_forever()