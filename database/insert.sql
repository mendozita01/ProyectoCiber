-- =========================================================
-- DATOS INICIALES
-- =========================================================
INSERT INTO empleados (
    documento_identidad, nombre, apellido, correo, telefono, direccion,
    usuario, password_hash, tipo_empleado
)
VALUES
('V-12345678', 'Adriana', 'Rojas', 'adriana.rojas@technova.local', '+58 412-1112233', 'Caracas, Venezuela', 'admin', MD5('Admin123'), 'admin'),
('V-23456789', 'Miguel', 'Hernández', 'miguel.hernandez@technova.local', '+58 414-2223344', 'Caracas, Venezuela', 'soporte1', MD5('Soporte123'), 'soporte'),
('V-34567890', 'Valeria', 'Castillo', 'valeria.castillo@technova.local', '+58 424-3334455', 'Caracas, Venezuela', 'analista1', MD5('Analista123'), 'analista');


INSERT INTO catalogo_diagnosticos (
    codigo, descripcion, nivel_alerta, recomendacion
)
VALUES
('OK-200', 'El equipo responde correctamente a las pruebas de conectividad.', 'baja', 'No requiere acción inmediata.'),
('HIGH_LATENCY', 'El equipo responde, pero presenta una latencia elevada.', 'media', 'Revisar conexión de red, cableado o saturación del enlace.'),
('HOST_DOWN', 'El equipo no responde a las pruebas de conectividad.', 'alta', 'Escalar el caso al área de soporte para revisión inmediata.'),
('IP_NOT_FOUND', 'La IP consultada no pertenece al inventario monitoreado.', 'media', 'Verificar si la IP fue escrita correctamente o si pertenece a la red del cliente.'),
('TIMEOUT', 'La consulta hacia el equipo superó el tiempo de espera.', 'alta', 'Revisar disponibilidad del equipo o posibles problemas de red.');


INSERT INTO diagnet_inventario_ips (
    ip, nombre_equipo, area, estado_equipo, latencia_ms, codigo_diagnostico
)
VALUES
('192.168.1.10', 'servidor-archivos', 'Infraestructura', 'activo', 18, 'OK-200'),
('192.168.1.20', 'router-principal', 'Redes', 'lento', 245, 'HIGH_LATENCY'),
('192.168.1.30', 'servidor-contabilidad', 'Administración', 'caido', NULL, 'HOST_DOWN'),
('192.168.1.40', 'equipo-recepcion', 'Atención al cliente', 'activo', 34, 'OK-200'),
('192.168.1.50', 'servidor-backup', 'Infraestructura', 'desconocido', NULL, 'TIMEOUT');


INSERT INTO tickets (
    nombre_solicitante, correo_solicitante, telefono_solicitante,
    empresa_solicitante, ip_reportada, descripcion_problema,
    estado, empleado_asignado_id,
    inventario_encontrado, nombre_equipo, area_equipo, estado_equipo,
    codigo_diagnostico, mensaje_diagnostico, nivel_alerta,
    recomendacion, latencia_ms
)
VALUES
('Carlos Pérez', 'carlos.perez@cliente.local', '+58 412-5551010', 'Comercial Pérez', '192.168.1.10', 'El usuario reporta lentitud al acceder al servidor de archivos.', 'diagnosticado', 2, TRUE, 'servidor-archivos', 'Infraestructura', 'activo', 'OK-200', 'El equipo responde correctamente a las pruebas de conectividad.', 'baja', 'No requiere acción inmediata.', 18),

('María González', 'maria.gonzalez@cliente.local', '+58 414-5552020', 'Contabilidad Global', '192.168.1.20', 'Se reporta lentitud general en la red.', 'diagnosticado', 2, TRUE, 'router-principal', 'Redes', 'lento', 'HIGH_LATENCY', 'El equipo responde, pero presenta una latencia elevada.', 'media', 'Revisar conexión de red, cableado o saturación del enlace.', 245),

('Luis Ramírez', 'luis.ramirez@cliente.local', '+58 424-5553030', 'Servicios Andinos', '192.168.1.30', 'No hay acceso al servidor de contabilidad.', 'diagnosticado', 3, TRUE, 'servidor-contabilidad', 'Administración', 'caido', 'HOST_DOWN', 'El equipo no responde a las pruebas de conectividad.', 'alta', 'Escalar el caso al área de soporte para revisión inmediata.', NULL),

('Ana Torres', 'ana.torres@cliente.local', '+58 412-5554040', 'Grupo Mérida', '192.168.1.40', 'El equipo de recepción presenta intermitencia.', 'diagnosticado', 2, TRUE, 'equipo-recepcion', 'Atención al cliente', 'activo', 'OK-200', 'El equipo responde correctamente a las pruebas de conectividad.', 'baja', 'No requiere acción inmediata.', 34);


INSERT INTO logs_eventos (
    evento, origen, ticket_id, empleado_id, detalle
)
VALUES
('CARGA_INICIAL', 'sistema', 1, 2, 'Ticket inicial diagnosticado mediante DiagNet.'),
('CARGA_INICIAL', 'sistema', 2, 2, 'Ticket inicial diagnosticado mediante DiagNet.'),
('CARGA_INICIAL', 'sistema', 3, 3, 'Ticket inicial diagnosticado mediante DiagNet.'),
('CARGA_INICIAL', 'sistema', 4, 2, 'Ticket inicial diagnosticado mediante DiagNet.');