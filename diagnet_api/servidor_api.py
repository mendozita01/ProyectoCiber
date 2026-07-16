import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Este diccionario (INVENTARIO) actúa como tu base de datos privada simulada.
INVENTARIO = {
    "192.168.0.50": {
        "hostname": "router-core",
        "estado": "activo",
        "latencia_ms": 18,
        "codigo_diagnostico": "OK-200",
        "mensaje": "Host activo y respondiendo"
    },
    "192.168.0.51": {
        "hostname": "switch-piso1",
        "estado": "alerta",
        "latencia_ms": 150,
        "codigo_diagnostico": "WARN-300",
        "mensaje": "Host con latencia alta"
    }
}

# Esta clase es el "portero" de tu servidor. Atiende a quienes te envían datos.
class DiagNetHandler(BaseHTTPRequestHandler):
    
    # Esta función se activa SOLO cuando alguien te envía datos usando el método POST.
    def do_POST(self):
        if self.path == '/diagnostico':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                ip_recibida = data.get('ip', '')
                
                print(f"[*] Revisando nuestro inventario interno para la IP: {ip_recibida}")
                
                # 4. Verificar si la IP existe en tu lista simulada (INVENTARIO)
                if ip_recibida in INVENTARIO:
                    # Si la IP está en tu lista, sacas sus datos y armas un JSON de éxito.
                    # El campo crítico aquí es "codigo_diagnostico", que es lo que el atacante alterará en el aire luego.
                    datos_equipo = INVENTARIO[ip_recibida]
                    respuesta = {
                        "ip_consultada": ip_recibida,
                        "inventario_encontrado": True,
                        "estado": datos_equipo["estado"],
                        "latencia_ms": datos_equipo["latencia_ms"],
                        "codigo_diagnostico": datos_equipo["codigo_diagnostico"]
                    }
                    print("    -> [RESULTADO] Equipo SI existe. Enviando diagnostico.")
                else:
                    # Si la IP no existe en tu lista, devuelves un JSON indicando el error.
                    respuesta = {
                        "ip_consultada": ip_recibida,
                        "inventario_encontrado": False,
                        "estado": "no_encontrado",
                        "latencia_ms": None,
                        "codigo_diagnostico": "IP_NOT_FOUND"
                    }
                    print("    -> [RESULTADO] Equipo NO existe en DiagNet.")
                
                # 5. Configurar el envío. El 200 significa "Todo salió bien con la petición HTTP".
                self.send_response(200)
                # Le decimos a la computadora de tu amiga que le vamos a enviar formato JSON.
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # 6. Convertir nuestra 'respuesta' a texto JSON y enviarla por la red.
                self.wfile.write(json.dumps(respuesta).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Peticion malformada"}')
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    # Le decimos al servidor que escuche en el puerto 8080 (0.0.0.0 significa que acepte conexiones de cualquier máquina virtual)
    server_address = ('0.0.0.0', 8080)
    httpd = HTTPServer(server_address, DiagNetHandler)
    
    print("===================================================")
    print("🛡️ API externa DiagNet corriendo en puerto 8080")
    print("===================================================")
    
    # Mantiene el servidor encendido y esperando peticiones para siempre
    httpd.serve_forever()