-- =========================================================
-- BASE DE DATOS: technova
-- Proyecto: technova / DiagNet
-- Motor: PostgreSQL
-- Versión vulnerable inicial
-- =========================================================
-- IMPORTANTE:
-- Este script se ejecuta dentro de la base de datos TechNova.
-- No crea la base de datos, solo crea tablas y secuencias .
-- =========================================================

DROP TABLE IF EXISTS logs_eventos;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS diagnet_inventario_ips;
DROP TABLE IF EXISTS catalogo_diagnosticos;
DROP TABLE IF EXISTS empleados;

DROP SEQUENCE IF EXISTS ticket_codigo_seq;

CREATE SEQUENCE ticket_codigo_seq
START WITH 1
INCREMENT BY 1;


CREATE TABLE empleados (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    documento_identidad VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(80) NOT NULL,
    apellido VARCHAR(80) NOT NULL,
    correo VARCHAR(120) NOT NULL UNIQUE,
    telefono VARCHAR(30),
    direccion TEXT,

    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,

    tipo_empleado VARCHAR(30) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_tipo_empleado
    CHECK (tipo_empleado IN ('admin', 'soporte', 'analista'))
);


CREATE TABLE catalogo_diagnosticos (
    codigo VARCHAR(50) PRIMARY KEY,

    descripcion TEXT NOT NULL,
    nivel_alerta VARCHAR(20) NOT NULL,
    recomendacion TEXT,

    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_nivel_alerta
    CHECK (nivel_alerta IN ('baja', 'media', 'alta', 'critica'))
);


CREATE TABLE diagnet_inventario_ips (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    ip VARCHAR(45) NOT NULL UNIQUE,
    nombre_equipo VARCHAR(120) NOT NULL,
    area VARCHAR(100) NOT NULL,
    estado_equipo VARCHAR(30) NOT NULL,
    latencia_ms INTEGER,

    codigo_diagnostico VARCHAR(50) NOT NULL,

    activo BOOLEAN NOT NULL DEFAULT TRUE,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_diagnet_catalogo
    FOREIGN KEY (codigo_diagnostico)
    REFERENCES catalogo_diagnosticos(codigo),

    CONSTRAINT chk_estado_equipo
    CHECK (estado_equipo IN ('activo', 'lento', 'caido', 'desconocido'))
);


CREATE TABLE tickets (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    codigo_ticket VARCHAR(20) NOT NULL UNIQUE
        DEFAULT ('TK-' || LPAD(nextval('ticket_codigo_seq')::TEXT, 6, '0')),

    nombre_solicitante VARCHAR(120) NOT NULL,
    correo_solicitante VARCHAR(120),
    telefono_solicitante VARCHAR(30),
    empresa_solicitante VARCHAR(120),

    ip_reportada VARCHAR(45) NOT NULL,
    descripcion_problema TEXT NOT NULL,

    estado VARCHAR(30) NOT NULL DEFAULT 'abierto',

    empleado_asignado_id INTEGER,

    inventario_encontrado BOOLEAN,
    nombre_equipo VARCHAR(120),
    area_equipo VARCHAR(100),
    estado_equipo VARCHAR(30),

    codigo_diagnostico VARCHAR(255),
    mensaje_diagnostico TEXT,
    nivel_alerta VARCHAR(20),
    recomendacion TEXT,
    latencia_ms INTEGER,

    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ticket_empleado
    FOREIGN KEY (empleado_asignado_id)
    REFERENCES empleados(id)
    ON DELETE SET NULL,

    CONSTRAINT chk_estado_ticket
    CHECK (estado IN ('abierto', 'en_revision', 'diagnosticado', 'asignado', 'cerrado'))
);


CREATE TABLE logs_eventos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    evento VARCHAR(80) NOT NULL,
    origen VARCHAR(80) NOT NULL,

    ticket_id INTEGER,
    empleado_id INTEGER,

    detalle TEXT,

    CONSTRAINT fk_log_ticket
    FOREIGN KEY (ticket_id)
    REFERENCES tickets(id)
    ON DELETE SET NULL,

    CONSTRAINT fk_log_empleado
    FOREIGN KEY (empleado_id)
    REFERENCES empleados(id)
    ON DELETE SET NULL
);