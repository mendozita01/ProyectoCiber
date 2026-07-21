-- =========================================================
-- DATOS INICIALES
TRUNCATE TABLE
    logs_eventos,
    tickets,
    diagnet_inventario_ips,
    catalogo_diagnosticos,
    empleados
RESTART IDENTITY CASCADE;

ALTER SEQUENCE ticket_codigo_seq RESTART WITH 1;

INSERT INTO empleados (
    documento_identidad, nombre, apellido, correo, telefono, direccion,
    usuario, password_hash, tipo_empleado
)
VALUES
('V-20568963', 'Andrea', 'Perez', 'andrea.perez@gmail.com', '+58 412-1000001', 'Caracas, Venezuela', 'admin', MD5('admin12'), 'admin'),
('V-10110032', 'Juan', 'Lopez', 'juan.lopez@hotmail.com', '+58 414-1000002', 'Caracas, Venezuela', 'soporte1', MD5('soporte123'), 'soporte'),
('V-18296546', 'Maria', 'Gonzalez', 'maria.gonzalez@gmail.com', '+58 424-1000003', 'Caracas, Venezuela', 'analista1', MD5('analista123'), 'analista'),
('V-22000202', 'Pedro', 'Ramirez', 'pedro.ramirez@hotmail.com', '+58 412-1000004', 'Caracas, Venezuela', 'pedro', MD5('pedro14'), 'soporte'),
('V-10080090', 'Carla', 'Torres', 'carla.torres@gmail.com', '+58 414-1000005', 'Caracas, Venezuela', 'carla', MD5('carla11'), 'analista'),
('V-26545966', 'Luis', 'Herrera', 'luis.herrera@hotmail.com', '+58 424-1000006', 'Caracas, Venezuela', 'luis', MD5('luis1234'), 'soporte'),
('V-19996350', 'Ana', 'Martinez', 'ana.martinez@gmail.com', '+58 412-1000007', 'Caracas, Venezuela', 'ana', MD5('ana123'), 'analista'),
('V-18998686', 'Jose', 'Castro', 'jose.castro@hotmail.com', '+58 414-1000008', 'Caracas, Venezuela', 'jose', MD5('jose0123'), 'soporte'),
('V-14100254', 'Sofia', 'Vargas', 'sofia.vargas@gmail.com', '+58 424-1000009', 'Caracas, Venezuela', 'sofia', MD5('sofia21'), 'analista'),
('V-10000450', 'Carlos', 'Mendoza', 'carlos.mendoza@hotmail.com', '+58 412-1000010', 'Caracas, Venezuela', 'carlos', MD5('carlos100'), 'soporte'),
('V-19077011', 'Laura', 'Silva', 'laura.silva@gmail.com', '+58 414-1000011', 'Caracas, Venezuela', 'laura', MD5('laura112'), 'analista'),
('V-29965012', 'Miguel', 'Rojas', 'miguel.rojas@hotmail.com', '+58 424-1000012', 'Caracas, Venezuela', 'miguel', MD5('miguel1234'), 'soporte'),
('V-10895013', 'Daniela', 'Flores', 'daniela.flores@gmail.com', '+58 412-1000013', 'Caracas, Venezuela', 'daniela', MD5('daniela22'), 'analista'),
('V-20055011', 'Roberto', 'Morales', 'roberto.morales@hotmail.com', '+58 414-1000014', 'Caracas, Venezuela', 'roberto', MD5('roberto23'), 'soporte'),
('V-18969457', 'Valeria', 'Ortiz', 'valeria.ortiz@gmail.com', '+58 424-1000015', 'Caracas, Venezuela', 'valeria', MD5('valeria2001'), 'analista'),
('V-27778987', 'Diego', 'Sanchez', 'diego.sanchez@hotmail.com', '+58 412-1000016', 'Caracas, Venezuela', 'diego', MD5('diego123'), 'soporte'),
('V-19636456', 'Natalia', 'Romero', 'natalia.romero@gmail.com', '+58 414-1000017', 'Caracas, Venezuela', 'natalia', MD5('natalia13'), 'analista'),
('V-14258963', 'Andres', 'Medina', 'andres.medina@hotmail.com', '+58 424-1000018', 'Caracas, Venezuela', 'andres', MD5('admin123'), 'admin'),
('V-25201203', 'Patricia', 'Gil', 'patricia.gil@gmail.com', '+58 412-1000019', 'Caracas, Venezuela', 'patricia', MD5('soporte15'), 'soporte'),
('V-10456000', 'Gabriel', 'Pena', 'gabriel.pena@hotmail.com', '+58 414-1000020', 'Caracas, Venezuela', 'gabriel', MD5('analista13'), 'analista');

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
('192.168.1.30', 'servidor-contabilidad', 'Administracion', 'caido', NULL, 'HOST_DOWN'),
('192.168.1.40', 'equipo-recepcion', 'Atencion al cliente', 'activo', 34, 'OK-200'),
('192.168.1.50', 'servidor-backup', 'Infraestructura', 'desconocido', NULL, 'TIMEOUT'),
('192.168.1.60', 'servidor-web', 'Infraestructura', 'activo', 22, 'OK-200'),
('192.168.1.70', 'switch-piso-2', 'Redes', 'lento', 310, 'HIGH_LATENCY'),
('192.168.1.80', 'servidor-facturacion', 'Administracion', 'caido', NULL, 'HOST_DOWN'),
('192.168.1.90', 'equipo-gerencia', 'Gerencia', 'activo', 15, 'OK-200'),
('192.168.1.100', 'servidor-reportes', 'Infraestructura', 'desconocido', NULL, 'TIMEOUT');

INSERT INTO tickets (
    nombre_solicitante, correo_solicitante, telefono_solicitante,
    empresa_solicitante, ip_reportada, descripcion_problema,
    estado, empleado_asignado_id,
    inventario_encontrado, nombre_equipo, area_equipo, estado_equipo,
    codigo_diagnostico, mensaje_diagnostico, nivel_alerta,
    recomendacion, latencia_ms
)
VALUES
(
    'Carlos Perez', 'carlos.perez@gmail.com', '+58 412-5551001',
    'Comercial Perez', '192.168.1.10', 'El usuario reporta lentitud al acceder al servidor de archivos.',
    'diagnosticado', 2,
    TRUE, 'servidor-archivos', 'Infraestructura', 'activo',
    'OK-200', 'El equipo responde correctamente a las pruebas de conectividad.', 'baja',
    'No requiere acción inmediata.', 18
),
(
    'Maria Castillo', 'maria.castillo@hotmail.com', '+58 414-5551002',
    'Mercado La Esquina', '192.168.1.40', 'El equipo de recepcion presenta intermitencia durante la mañana.',
    'diagnosticado', 6,
    TRUE, 'equipo-recepcion', 'Atencion al cliente', 'activo',
    'OK-200', 'El equipo responde correctamente a las pruebas de conectividad.', 'baja',
    'No requiere acción inmediata.', 34
),
(
    'Luis Ramirez', 'luis.ramirez@gmail.com', '+58 424-5551003',
    'Servicios Andinos', '192.168.1.20', 'Se reporta lentitud general en la red de la empresa.',
    'en_revision', 2,
    TRUE, 'router-principal', 'Redes', 'lento',
    'HIGH_LATENCY', 'El equipo responde, pero presenta una latencia elevada.', 'media',
    'Revisar conexión de red, cableado o saturación del enlace.', 245
),
(
    'Ana Torres', 'ana.torres@hotmail.com', '+58 412-5551004',
    'Grupo Merida', '192.168.1.30', 'No hay acceso al servidor de contabilidad.',
    'en_revision', 4,
    TRUE, 'servidor-contabilidad', 'Administracion', 'caido',
    'HOST_DOWN', 'El equipo no responde a las pruebas de conectividad.', 'alta',
    'Escalar el caso al área de soporte para revisión inmediata.', NULL
),
(
    'Jorge Castillo', 'jorge.castillo@gmail.com', '+58 414-5551005',
    'Farmacia Santa Lucia', '192.168.1.50', 'El sistema de respaldo no responde a las solicitudes del area administrativa.',
    'asignado', 5,
    TRUE, 'servidor-backup', 'Infraestructura', 'desconocido',
    'TIMEOUT', 'La consulta hacia el equipo superó el tiempo de espera.', 'alta',
    'Revisar disponibilidad del equipo o posibles problemas de red.', NULL
),
(
    'Paola Ruiz', 'paola.ruiz@hotmail.com', '+58 424-5551006',
    'Clinica Santa Ana', '192.168.1.70', 'El enlace del segundo piso presentaba latencia elevada y fue escalado para correccion.',
    'cerrado', 13,
    TRUE, 'switch-piso-2', 'Redes', 'lento',
    'HIGH_LATENCY', 'El equipo responde, pero presenta una latencia elevada.', 'media',
    'Revisar conexión de red, cableado o saturación del enlace.', 310
);

INSERT INTO logs_eventos (
    evento, origen, ticket_id, empleado_id, detalle
)
VALUES
('TICKET_DIAGNOSTICADO', 'sistema', 1, 2, 'DiagNet confirmó OK-200. El ticket quedó registrado sin falla técnica detectada.'),
('TICKET_DIAGNOSTICADO', 'sistema', 2, 6, 'DiagNet confirmó OK-200. El equipo reportado responde correctamente.'),
('TICKET_EN_REVISION', 'sistema', 3, 2, 'DiagNet detectó HIGH_LATENCY. El ticket quedó pendiente para soporte Nivel 1.'),
('TICKET_EN_REVISION', 'sistema', 4, 4, 'DiagNet detectó HOST_DOWN. El ticket quedó pendiente para soporte Nivel 1.'),
('TICKET_EN_REVISION', 'sistema', 5, 2, 'DiagNet detectó TIMEOUT. Soporte Nivel 1 revisó el incidente.'),
('TICKET_ESCALADO', 'soporte', 5, 2, 'Soporte Nivel 1 usó el modal Escalar Incidente y envió el caso a un analista.'),
('TICKET_EN_REVISION', 'sistema', 6, 6, 'DiagNet detectó HIGH_LATENCY. El caso fue revisado por soporte Nivel 1.'),
('TICKET_CERRADO', 'soporte', 6, 13, 'El problema fue solucionado exitosamente y el ticket quedó archivado.');