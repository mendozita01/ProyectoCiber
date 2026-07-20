#!/bin/bash
# =========================================================
# Genera certificados TLS autofirmados para el laboratorio.
#
# Contramedida (A04 / API10): reemplaza el trafico HTTP en
# claro por HTTPS entre TechNova y DiagNet, y entre el
# navegador y TechNova (login).
#
# Uso: ejecutar una sola vez antes de levantar los servicios.
#   bash certs/generar_certs.sh
# =========================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

generar() {
    NOMBRE=$1
    CN=$2
    if [ -f "${NOMBRE}.crt" ]; then
        echo "[-] ${NOMBRE}.crt ya existe, se omite."
        return
    fi
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "${NOMBRE}.key" \
        -out "${NOMBRE}.crt" \
        -days 365 \
        -subj "/C=VE/O=TechNovaLab/CN=${CN}" \
        -addext "subjectAltName=DNS:${CN},DNS:localhost,IP:127.0.0.1"
    echo "[+] Generado ${NOMBRE}.crt / ${NOMBRE}.key (CN=${CN})"
}

generar technova technova.local
generar diagnet diagnet.local

echo ""
echo "Certificados listos en $DIR"
echo "TechNova validara la identidad de DiagNet usando diagnet.crt (certificate pinning)."
