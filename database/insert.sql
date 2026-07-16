-- =========================================================
-- DATOS INICIALES
-- =========================================================

INSERT INTO empleados
(documento_identidad, nombre, apellido, correo, telefono, direccion, usuario, password_hash, tipo_empleado)
VALUES
('V-12345678', 'Adriana', 'Rojas', 'adriana.rojas@technova.local', '04141234567', 'Caracas, Venezuela', 'admin', MD5('Admin123'), 'admin'),

('V-23456789', 'Miguel', 'Hernández', 'miguel.hernandez@technova.local', '04149876543', 'Caracas, Venezuela', 'soporte1', MD5('Soporte123'), 'soporte'),

('V-34567890', 'Valeria', 'Castillo', 'valeria.castillo@technova.local', '04145556677', 'Caracas, Venezuela', 'analista1', MD5('Analista123'), 'analista');

INSERT INTO catalogo_diagnosticos
(codigo, descripcion, nivel_alerta, recomendacion)
VALUES
('OK-200', 'El equipo se encuentra activo y responde correctamente.', 'baja', 'No requiere acción inmediata.'),

('HIGH_LATENCY', 'El equipo responde, pero presenta latencia elevada.', 'media', 'Revisar conectividad interna o posible congestión en la red.'),

('HOST_DOWN', 'El equipo no responde a las pruebas de conectividad.', 'alta', 'Escalar el caso al área de soporte de infraestructura.'),

('IP_NOT_FOUND', 'La IP consultada no pertenece al inventario monitoreado.', 'media', 'Verificar si la IP fue escrita correctamente o si pertenece a otra sede.'),

('TIMEOUT', 'La consulta hacia el equipo superó el tiempo de espera.', 'alta', 'Reintentar el diagnóstico y revisar disponibilidad del segmento de red.');

INSERT INTO diagnet_inventario_ips
(ip, nombre_equipo, area, estado_equipo, latencia_ms, codigo_diagnostico)
VALUES
('192.168.1.10', 'servidor-archivos', 'Infraestructura', 'activo', 18, 'OK-200'),

('192.168.1.20', 'router-principal', 'Redes', 'lento', 245, 'HIGH_LATENCY'),

('192.168.1.30', 'servidor-contabilidad', 'Administración', 'caido', NULL, 'HOST_DOWN'),

('192.168.1.40', 'equipo-recepcion', 'Atención al cliente', 'activo', 34, 'OK-200'),

('192.168.1.50', 'servidor-backup', 'Infraestructura', 'desconocido', NULL, 'TIMEOUT');

INSERT INTO tickets
(nombre_solicitante, correo_solicitante, telefono_solicitante, empresa_solicitante, ip_reportada, descripcion_problema, estado, empleado_asignado_id, codigo_diagnostico, mensaje_diagnostico, latencia_ms)
VALUES
('Carlos Pérez', 'carlos.perez@comercialperez.com', '04140001111', 'Comercial Pérez', '192.168.1.10', 'No puedo acceder al servidor de archivos de la empresa.', 'diagnosticado', 2, 'OK-200', 'El equipo se encuentra activo y responde correctamente.', 18),

('María González', 'maria.gonzalez@contabilidadglobal.com', '04140002222', 'Contabilidad Global', '192.168.1.20', 'El sistema responde muy lento desde la oficina principal.', 'diagnosticado', 2, 'HIGH_LATENCY', 'El equipo responde, pero presenta latencia elevada.', 245),

('Luis Ramírez', 'luis.ramirez@serviciosandinos.com', '04140003333', 'Servicios Andinos', '192.168.1.30', 'No hay respuesta desde el servidor de contabilidad.', 'diagnosticado', 3, 'HOST_DOWN', 'El equipo no responde a las pruebas de conectividad.', NULL),

('Ana Torres', 'ana.torres@grupomerida.com', '04140004444', 'Grupo Mérida', '192.168.1.40', 'El equipo de recepción presenta fallas intermitentes de conexión.', 'diagnosticado', 2, 'OK-200', 'El equipo se encuentra activo y responde correctamente.', 34);

INSERT INTO logs_eventos
(evento, origen, ticket_id, empleado_id, detalle)
VALUES
('INICIALIZACION_BD', 'sistema', NULL, NULL, 'Base de datos TechNova inicializada correctamente.'),

('CARGA_DATOS_PRUEBA', 'sistema', NULL, NULL, 'Datos iniciales cargados para empleados, diagnósticos, inventario y tickets.'),

('TICKET_CREADO', 'portal_publico', 1, NULL, 'Ticket TK-000001 creado desde el portal público.'),

('DIAGNOSTICO_RECIBIDO', 'diagnet_api', 1, NULL, 'DiagNet devolvió el código OK-200 para la IP 192.168.1.10.'),

('TICKET_CREADO', 'portal_publico', 2, NULL, 'Ticket TK-000002 creado desde el portal público.'),

('DIAGNOSTICO_RECIBIDO', 'diagnet_api', 2, NULL, 'DiagNet devolvió el código HIGH_LATENCY para la IP 192.168.1.20.'),

('LOGIN_EXITOSO', 'panel_admin', NULL, 1, 'Inicio de sesión exitoso del usuario admin.');