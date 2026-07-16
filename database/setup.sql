CREATE DATABASE technova_db;
\c technova_db;  -- En postgres se usa \c para usar la base de datos, no USE

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY, -- ¡Cambio importante aquí!
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY, -- ¡Cambio importante aquí!
    ip_reportada VARCHAR(50),
    codigo_diagnostico VARCHAR(255)
);

INSERT INTO usuarios (username, password_hash) VALUES ('admin', md5('secreto123'));