const express = require('express');
const app = express();

app.get('/api/diagnostico', (req, res) => {
    res.json({
        "status": "ok", 
        "codigo_diagnostico": "DIAG-550"
    });
});

app.listen(80, '0.0.0.0', () => {
    console.log('DiagNet API corriendo en http://0.0.0.0:80 (INSEGURO)');
});
