CREATE DATABASE technova_db;
USE technova_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_reportada VARCHAR(50),
    codigo_diagnostico VARCHAR(255)
);

INSERT INTO usuarios (username, password_hash) 
VALUES ('admin', MD5('secreto123'));
