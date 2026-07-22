#!/bin/bash
# =========================================================
# Genera certificados TLS autofirmados para el laboratorio.
#
# Contramedida (A04 / API10): reemplaza el trafico HTTP en
# claro por HTTPS entre TechNova y DiagNet, y entre el
# navegador y TechNova (login y panel).
#
# En la version asegurada, TechNova valida el certificado
# conocido de DiagNet antes de procesar la respuesta de la API.
# Esto evita aceptar un servicio externo suplantado durante la
# simulacion de ataque.
#
# Uso: ejecutar antes de levantar los servicios o cuando cambien
# las IP de las maquinas virtuales.
#   bash certs/generar_certs.sh
# =========================================================

set -e
export MSYS_NO_PATHCONV=1
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

generar() {
    NOMBRE=$1
    CN=$2
    IP_VM=$3

    echo "[*] Generando certificado para ${NOMBRE}..."

    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "${NOMBRE}.key" \
        -out "${NOMBRE}.crt" \
        -days 365 \
        -subj "/C=VE/O=TechNovaLab/CN=${CN}" \
        -addext "subjectAltName=DNS:${CN},DNS:localhost,IP:127.0.0.1,IP:${IP_VM}"

    echo "[+] Generado ${NOMBRE}.crt / ${NOMBRE}.key"
    echo "    CN=${CN}"
    echo "    SAN=DNS:${CN}, DNS:localhost, IP:127.0.0.1, IP:${IP_VM}"
}

# TechNova corre en la VM 192.168.0.4 por el puerto 3000.
# Se incluye technova.local, localhost, 127.0.0.1 y la IP real
# de la VM para permitir pruebas locales y pruebas desde Kali.
generar technova technova.local 192.168.0.4

# DiagNet corre en la VM 192.168.0.5 por el puerto 8080.
# Esta IP es importante porque TechNova consume la API usando
# https://192.168.0.5:8080 y valida el certificado diagnet.crt.
generar diagnet diagnet.local 192.168.0.5

echo ""
echo "Certificados listos en $DIR"
echo "TechNova validara la identidad de DiagNet usando diagnet.crt."
