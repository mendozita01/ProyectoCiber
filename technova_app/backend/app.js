
const express = require('express');
const mysql = require('mysql2');
const axios = require('axios');
const app = express();

app.use(express.urlencoded({ extended: true }));
app.use(express.static('../frontend'));

const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: '',
    database: 'technova_db'
});

app.post('/crear_ticket', async (req, res) => {
    const ip_reportada = req.body.ip_reportada;

    try {
        // VULNERABILIDAD API10: El consumo no valida integridad ni autenticidad.
        const respuesta_diagnet = await axios.get('http://192.168.0.5/api/diagnostico'); 
        const codigo = respuesta_diagnet.data.codigo_diagnostico;

        // VULNERABILIDAD (Inyección SQL): Esta línea es insegura porque concatena directamente la entrada con la consulta SQL. Faltan procesos de aseguramiento.
        const query = "INSERT INTO tickets (ip_reportada, codigo_diagnostico) VALUES ('" + ip_reportada + "', '" + codigo + "')";

        db.query(query, (err, result) => {
            if (err) {
                // VULNERABILIDAD A10 (Gestión deficiente de condiciones de excepción): Mostrar el error de SQL expone detalles técnicos de la arquitectura.
                return res.send("Error SQL: " + err.message); 
            }
            res.send("<h1>Ticket creado. Código: " + codigo + "</h1>");
        });
    } catch (error) {
        res.send("Error de red: " + error.message);
    }
});

app.listen(3000, '0.0.0.0', () => {
    console.log('TechNova corriendo en puerto 3000');
});