const express = require('express');
const mysql = require('mysql2');
const axios = require('axios');
const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.static('../frontend'));

// Configuración de la conexión a la base de datos
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root', 
    password: '', // ¡Asegúrate que coincida con tu password de MariaDB!
    database: 'technova_db'
});

// Prueba de conexión antes de iniciar
db.connect((err) => {
    if (err) {
        console.error('❌ Error conectando a la base de datos:');
        console.error('Código de error:', err.code);
        console.error('Mensaje:', err.message);
        console.error('¿Está encendido MariaDB/MySQL? ¿La contraseña es correcta?');
    } else {
        console.log('✅ Conectado a la base de datos MariaDB');
    }
});

app.post('/crear_ticket', async (req, res) => {
    const ip_reportada = req.body.ip_reportada;

    try {
        // Solicitud a la API externa (Inseguro - HTTP plano)
        // Asegúrate de que esta IP sea la IP real de tu VM de DiagNet
        const respuesta_diagnet = await axios.get('http://192.168.0.5/api/diagnostico'); 
        const codigo = respuesta_diagnet.data.codigo_diagnostico;

        // VULNERABILIDAD CWE-89 (Inyección SQL por concatenación)
        // El atacante manipulará el valor de 'codigo' vía Man-in-the-Middle
        const query = "INSERT INTO tickets (ip_reportada, codigo_diagnostico) VALUES ('" + ip_reportada + "', '" + codigo + "')";

        db.query(query, (err, result) => {
            if (err) {
                // Falla: Se muestra el error técnico al usuario
                return res.send("<h1>Error técnico</h1><p>" + err.message + "</p>"); 
            }
            res.send("<h1>Ticket creado. Código: " + codigo + "</h1>");
        });

    } catch (error) {
        res.send("<h1>Error de comunicación con la API:</h1><p>" + error.message + "</p>");
    }
});

app.listen(3000, '0.0.0.0', () => {
    console.log('TechNova App corriendo en puerto 3000');
});