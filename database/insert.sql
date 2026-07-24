-- =========================================================
-- DATOS INICIALES - RAMA ASEGURADA
-- =========================================================
-- CONTRAMEDIDA (A04 - Fallas Criptográficas):
-- Las contraseñas ya no se almacenan ni se calculan con MD5.
--
-- En esta versión se insertan hashes generados previamente con
-- PBKDF2-HMAC-SHA256 usando la biblioteca estándar de Python.
--
-- Formato del hash almacenado:
-- pbkdf2_sha256$iteraciones$salt$hash
--
-- Cada contraseña tiene un salt único y un número alto de
-- iteraciones, lo que aumenta el costo de ataques de diccionario
-- sobre hashes extraídos.
--
-- Las contraseñas en texto plano se mantienen únicamente como
-- credenciales de demostración para la práctica académica, pero
-- no se almacenan directamente en la base de datos.
--
-- Para generar nuevos hashes de prueba se puede usar:
-- technova_app/backend/generar_hash.py
-- =========================================================
-- Credenciales demo para pruebas controladas:
-- admin      -> admin12
-- soporte1   -> soporte123
-- analista1  -> analista123


TRUNCATE TABLE
    logs_eventos,
    tickets,
    diagnet_inventario_ips,
    catalogo_diagnosticos,
    empleados
RESTART IDENTITY CASCADE;




-- Rama asegurada:
-- Las contraseñas ya no se almacenan con MD5.
-- Se guardan hashes PBKDF2-HMAC-SHA256 con salt único e iteraciones.
INSERT INTO empleados (
    documento_identidad, nombre, apellido, correo, telefono, direccion,
    usuario, password_hash, tipo_empleado
)
VALUES
('V-20568963', 'Andrea', 'Perez', 'andrea.perez@gmail.com', '+58 412-1000001', 'Caracas, Venezuela', 'admin', 'pbkdf2_sha256$150000$91f13b419a197f7fab06a5737244c491$23ee89df0f7440bba47824481dc6cdc082ea269a3caa4afe587ea0bcd346252d', 'admin'),
('V-10110032', 'Juan', 'Lopez', 'juan.lopez@hotmail.com', '+58 414-1000002', 'Caracas, Venezuela', 'soporte1', 'pbkdf2_sha256$150000$5b6f5c283d748a528b3b37c445e8774a$9e9be20720172981f17fac840c1ac41b813cec3f4a4b0f0864ec9b34c33f6057', 'soporte'),
('V-18296546', 'Maria', 'Gonzalez', 'maria.gonzalez@gmail.com', '+58 424-1000003', 'Caracas, Venezuela', 'analista1', 'pbkdf2_sha256$150000$79ed7f1a6b3e9604d72a730d9c65aa7b$72c6e28e6cc6eb613c9571b0b7bf6ed861428cb8288a317169683d6679db3052', 'analista'),
('V-22000202', 'Pedro', 'Ramirez', 'pedro.ramirez@hotmail.com', '+58 412-1000004', 'Caracas, Venezuela', 'pedro', 'pbkdf2_sha256$150000$8217d0d691ecf382e3ae2f39eeba9706$d14e513f1b48c773a75b5fdd43a67f70396b6a7357b40fd3c85ca7b1c7b7bee3', 'soporte'),
('V-10080090', 'Carla', 'Torres', 'carla.torres@gmail.com', '+58 414-1000005', 'Caracas, Venezuela', 'carla', 'pbkdf2_sha256$150000$c4d2511ccc63fbf40525d51dc0298949$e04e67208a6e96bcad335594338fc927799ddf41db0532669c2f04b51cbc2a34', 'analista'),
('V-26545966', 'Luis', 'Herrera', 'luis.herrera@hotmail.com', '+58 424-1000006', 'Caracas, Venezuela', 'luis', 'pbkdf2_sha256$150000$fbfe8acdc5320e1c803fc5233b7f219a$c55a1cf1a28d2442fc5aa67656fbef79551dafc8b5f7033c6ca9a9f4b71688a7', 'soporte'),
('V-19996350', 'Ana', 'Martinez', 'ana.martinez@gmail.com', '+58 412-1000007', 'Caracas, Venezuela', 'ana', 'pbkdf2_sha256$150000$b16f4cd33bd4e5c758256e0a1b46e10d$28a99ee20a366b788a6208451ff3b8eb80b3f789176e10c701ba8ba8a2567984', 'analista'),
('V-18998686', 'Jose', 'Castro', 'jose.castro@hotmail.com', '+58 414-1000008', 'Caracas, Venezuela', 'jose', 'pbkdf2_sha256$150000$ee99494acc0bbb19562b945830bba1dc$ae9e4a7c653d0266092a7040b6bc59573b33554eea62035abe9d510ab411bb5c', 'soporte'),
('V-14100254', 'Sofia', 'Vargas', 'sofia.vargas@gmail.com', '+58 424-1000009', 'Caracas, Venezuela', 'sofia', 'pbkdf2_sha256$150000$6c64b61682556c654229c0e10646dc97$882e189f411d8400239321aab1ec42138ed75755f2d71cd20a3c830e40a41c1a', 'analista'),
('V-10000450', 'Carlos', 'Mendoza', 'carlos.mendoza@hotmail.com', '+58 412-1000010', 'Caracas, Venezuela', 'carlos', 'pbkdf2_sha256$150000$205b9eca3687587cf07295f1808f73bb$0d25d040883a77e69029f6389c3d3d38c5fc75764b2805e516eee674f6814b56', 'soporte'),
('V-19077011', 'Laura', 'Silva', 'laura.silva@gmail.com', '+58 414-1000011', 'Caracas, Venezuela', 'laura', 'pbkdf2_sha256$150000$b57eb38246795d25eaddd8577588bfd3$ceb4b5786980ead37594fd017c7ee1e6d6b6f7506c315a59c0bcaf88f21cae93', 'analista'),
('V-29965012', 'Miguel', 'Rojas', 'miguel.rojas@hotmail.com', '+58 424-1000012', 'Caracas, Venezuela', 'miguel', 'pbkdf2_sha256$150000$82a0188cdc432838f225e44fa65e17d5$713baea9b9ff9f2bcb9e2a2a125773daeb0b0ab9f4c5c98eb0852cdb24e0b42d', 'soporte'),
('V-10895013', 'Daniela', 'Flores', 'daniela.flores@gmail.com', '+58 412-1000013', 'Caracas, Venezuela', 'daniela', 'pbkdf2_sha256$150000$8f6e2d233d56c42ea0c8edbeb00e35aa$0a28a8f92a00b58af1aa3e2472e16def478f1612bf4791c99fb7608988d1abea', 'analista'),
('V-20055011', 'Roberto', 'Morales', 'roberto.morales@hotmail.com', '+58 414-1000014', 'Caracas, Venezuela', 'roberto', 'pbkdf2_sha256$150000$9706fa08681118718df47218794cc09a$8ebd4d990990bf386f2210a8f074b1d4e092b098305b2f513dc8aaf541beb2f2', 'soporte'),
('V-18969457', 'Valeria', 'Ortiz', 'valeria.ortiz@gmail.com', '+58 424-1000015', 'Caracas, Venezuela', 'valeria', 'pbkdf2_sha256$150000$f174fb3310e07bc8a7a4d0593df05799$363cbfab2825ba1118b926eea9fa787a5d07222294e40db87cdc7a7208857e32', 'analista'),
('V-27778987', 'Diego', 'Sanchez', 'diego.sanchez@hotmail.com', '+58 412-1000016', 'Caracas, Venezuela', 'diego', 'pbkdf2_sha256$150000$bc12a3c66fdbc404050ae825f47502ef$f0c48ebd4c167084f142e2cee11469ad9cd98b157caed1f848c6030de25bc89e', 'soporte'),
('V-19636456', 'Natalia', 'Romero', 'natalia.romero@gmail.com', '+58 414-1000017', 'Caracas, Venezuela', 'natalia', 'pbkdf2_sha256$150000$8ff4984e0ae5306680218f57cfbe0a9d$a99419fc22ce96ef8a96d46303c95652cfe1e9bc5834935621fb3d0844488933', 'analista'),
('V-14258963', 'Andres', 'Medina', 'andres.medina@hotmail.com', '+58 424-1000018', 'Caracas, Venezuela', 'andres', 'pbkdf2_sha256$150000$d5769f87cffb7f57583788d61365d9da$88a73a1bd6d5304ac352ea95d48619121d1871e5d89a32872daa94b26ba86240', 'admin'),
('V-25201203', 'Patricia', 'Gil', 'patricia.gil@gmail.com', '+58 412-1000019', 'Caracas, Venezuela', 'patricia', 'pbkdf2_sha256$150000$7d9aa1fc03ff8bd8a226c03160124da4$29bd040fb08ef914931b6028609a83152a8b8f581cf76c80ac507d1e1ce304a9', 'soporte'),
('V-10456000', 'Gabriel', 'Pena', 'gabriel.pena@hotmail.com', '+58 414-1000020', 'Caracas, Venezuela', 'gabriel', 'pbkdf2_sha256$150000$2e856d8de17cd5720b12d969b3ac5c05$467b55825732edf1efce91a46fd7b1d0a23360afe819a49039dd12287984d6cb', 'analista');
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