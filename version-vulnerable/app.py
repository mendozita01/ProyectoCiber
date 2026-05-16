from flask import Flask, render_template_string, request, redirect, url_for
import hashlib

app = Flask(__name__)

# --- RUTA 1: LOGIN VULNERABLE (Falla Criptográfica) ---
@app.route('/', methods=['GET', 'POST'])
def login():
    mensaje = ""
    if request.method == 'POST':
        usuario = request.form['username']
        password = request.form['password']
        
        # VULNERABILIDAD 1: MD5 sin salt
        hash_vulnerable = hashlib.md5(password.encode()).hexdigest()
        
        # Simularemos que el login es correcto para pasar al panel
        return redirect(url_for('dashboard', user=usuario))

    formulario_html = f'''
        <h2>Portal TechNova - Acceso de Técnicos</h2>
        {mensaje}
        <form method="POST">
            Usuario: <input type="text" name="username" required><br><br>
            Clave: <input type="password" name="password" required><br><br>
            <input type="submit" value="Entrar al Portal">
        </form>
    '''
    return render_template_string(formulario_html)


# --- RUTA 2: PANEL DE DIAGNÓSTICO (Consumo Inseguro de API) ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    usuario = request.args.get('user', 'Técnico')
    resultado_api = ""
    
    if request.method == 'POST':
        ip_ingresada = request.form['ip_diagnostico']
        
        # VULNERABILIDAD 2: Consumo Inseguro y Confianza Ciega
        # Simulamos la respuesta de una API externa en formato JSON. 
        # El backend toma la variable "ip_ingresada" y la concatena directo en el HTML sin limpiarla.
        respuesta_simulada = f'{{"status": "error", "ip_objetivo": "{ip_ingresada}", "mensaje": "Host inalcanzable"}}'
        
        resultado_api = f'''
            <div style="background-color: #ffcccc; padding: 10px; margin-top: 20px;">
                <h4>Respuesta cruda de la API Externa:</h4>
                <p>{respuesta_simulada}</p>
            </div>
        '''

    dashboard_html = f'''
        <h2>Panel de Diagnóstico TechNova</h2>
        <p>Bienvenido, <b>{usuario}</b></p>
        <hr>
        <h3>Diagnosticar equipo en la red:</h3>
        <form method="POST">
            IP del equipo: <input type="text" name="ip_diagnostico" placeholder="Ej: 192.168.1.50" required size="40">
            <input type="submit" value="Enviar a API Externa">
        </form>
        {resultado_api}
        <br><br>
        <a href="/">Cerrar Sesión</a>
    '''
    return render_template_string(dashboard_html)

# --- ARRANCAR EL SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)