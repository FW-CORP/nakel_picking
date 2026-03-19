# Diagnóstico: PDF no refleja nakel_picking y error de actualización

## 1. Error de conexión PostgreSQL al actualizar

```
psycopg2.OperationalError: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: fe_sendauth: no password supplied
```

**Causa:** Odoo intenta conectarse a PostgreSQL sin credenciales. El comando `odoo` usa configuración por defecto.

**Solución:** Usar el archivo de configuración de Odoo que tiene las credenciales:

```bash
# Opción A: Si Odoo usa un archivo de configuración (ej. /etc/odoo/odoo.conf)
odoo -c /etc/odoo/odoo.conf -u nakel_picking -d master_18 --stop-after-init

# Opción B: Si usas systemd, el servicio ya tiene la config. Actualizar desde la interfaz:
# Aplicaciones → Buscar "Nakel Picking" → Actualizar

# Opción C: Variables de entorno
export PGPASSWORD=tu_password
odoo -u nakel_picking -d master_18 --stop-after-init
```

**Verificar configuración:** Revisar en `/etc/odoo/odoo.conf` o donde esté tu config:
- `db_host`
- `db_user`
- `db_password`
- `db_name` (o usar `-d master_18`)

---

## 2. PDF no muestra el formato de nakel_picking

### Posibles causas

| Causa | Descripción | Cómo verificar |
|-------|-------------|----------------|
| **A. Módulo no actualizado** | La actualización falló por PostgreSQL, el módulo sigue en versión antigua | En Odoo: Ajustes → Aplicaciones → Nakel Picking → ver versión |
| **B. XPath no coincide** | Odoo 18 puede tener estructura distinta en `stock_picking_batch.report_picking_batch` | Revisar logs al imprimir; si hay error de template |
| **C. move_line_ids vacíos** | Los pickings no tienen operaciones detalladas; `_get_consolidated_lines()` usa `move_line_ids` | Si los traslados están en "Esperando" o "Asignado" sin "Comprobar disponibilidad" |
| **D. Reporte estándar se usa** | Otro módulo o caché usa el reporte original | Limpiar caché del navegador; reiniciar Odoo |

### Si ves solo flechas (→) en el PDF

Las flechas vienen de la columna **Paquete** cuando no hay paquete asignado:
```xml
<span>→ <span t-esc="line['result_package_name'] or 'PACK0000002'"/></span>
```

Eso indica que **el template de nakel_picking SÍ se está usando**, pero:
- La sección "Productos Consolidados" puede estar vacía si `move_line_ids` está vacío
- O las tablas se renderizan mal en el PDF

### Si ves el reporte estándar (sin "Resumen:", sin "Productos Consolidados")

Entonces el template de nakel_picking **no se está aplicando**. Posibles motivos:
1. Módulo no actualizado correctamente
2. XPath no coincide con la estructura de Odoo 18
3. Orden de carga: otro módulo sobrescribe después

---

## 3. Pasos de diagnóstico

### Paso 1: Verificar que el módulo está instalado y actualizado

```bash
# En Odoo (shell o desde psql)
# O desde la interfaz: Aplicaciones → Nakel Picking → debe estar "Instalado"
```

### Paso 2: Verificar estado de los pickings del lote

Antes de imprimir, en el lote:
- Los traslados deben tener **operaciones detalladas** (move_line_ids)
- Si están en "Esperando" o "Asignado", hacer clic en **"Comprobar disponibilidad"** para generar move_line_ids

### Paso 3: Revisar logs de Odoo al imprimir

```bash
# Al imprimir el reporte, revisar:
tail -f /var/log/odoo/odoo-server.log
# O si usas docker:
docker-compose logs -f odoo
```

Buscar errores relacionados con `nakel_picking`, `report_picking_batch` o `_get_consolidated_lines`.

### Paso 4: Actualizar con configuración correcta

```bash
# Usar el config de producción
sudo -u odoo odoo -c /etc/odoo/odoo.conf -u nakel_picking -d master_18 --stop-after-init
```

---

## 4. Cambios aplicados (v18.0.1.2.0)

1. **Fallback a move_ids** (`models/stock_picking_batch.py`): Si los pickings no tienen `move_line_ids` (operaciones detalladas), ahora se usan `move_ids` para generar la sección "Productos Consolidados". Así el reporte muestra datos aunque no se haya hecho "Comprobar disponibilidad".

2. **Secuencia en tabla de traslados** (`reports/stock_picking_batch_report.xml`): La columna "Secuencia" ahora muestra 1, 2, 3... en lugar de 0, 1, 2...

### Cómo desplegar los cambios en producción

1. Copiar el módulo actualizado a `/usr/lib/python3/dist-packages/odoo/addons/nakel_picking/`
2. Actualizar con config correcta:
   ```bash
   sudo -u odoo odoo -c /etc/odoo/odoo.conf -u nakel_picking -d master_18 --stop-after-init
   ```
3. O desde la interfaz: Aplicaciones → Nakel Picking → Actualizar
