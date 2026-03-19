#!/bin/bash
# Despliegue de nakel_picking al servidor Odoo
# Uso: ./deploy.sh [host]
# Ejemplo: ./deploy.sh odoo-ct-nakel
#
# Nota: ssh -t asigna TTY para que sudo pueda pedir contraseña.
# Para despliegue sin contraseña, configura en el servidor:
#   echo "odoo ALL=(ALL) NOPASSWD: /usr/bin/cp, /usr/bin/chown" | sudo tee /etc/sudoers.d/odoo-deploy

set -e
HOST="${1:-odoo-ct-nakel}"
MODULE_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_ADDONS="/usr/lib/python3/dist-packages/odoo/addons/nakel_picking"

echo "📦 Desplegando nakel_picking a $HOST..."
echo ""

# 1. Sincronizar archivos a /tmp en el servidor
echo "1️⃣  Sincronizando archivos..."
rsync -avz --exclude='.git' --exclude='deploy.sh' \
    "$MODULE_DIR/" \
    "$HOST:/tmp/nakel_picking/"

# 2. Copiar a addons (requiere sudo en el servidor)
#    -t asigna TTY para que sudo pueda pedir contraseña si hace falta
echo ""
echo "2️⃣  Copiando a addons de Odoo (puede pedir contraseña sudo)..."
ssh -t "$HOST" "sudo cp -r /tmp/nakel_picking/* $REMOTE_ADDONS/ && sudo chown -R odoo:odoo $REMOTE_ADDONS && echo '✅ Archivos copiados correctamente'"

echo ""
echo "✅ Despliegue completado."
echo ""
echo "Para actualizar el módulo en Odoo:"
echo "  ssh -t $HOST \"sudo systemctl stop odoo && sudo -u odoo odoo -c /etc/odoo/odoo.conf -u nakel_picking -d master_18 --stop-after-init && sudo systemctl start odoo\""
echo ""
echo "O desde la interfaz: Aplicaciones → Nakel Picking → Actualizar"
