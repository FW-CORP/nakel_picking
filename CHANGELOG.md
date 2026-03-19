# Changelog

Todos los cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

---

## [18.0.1.9.0] - 2025-03-19

### Corregido

- **Salto de página**: Evita encabezados huérfanos al final de página. Cada sección de ruta (cabecera + tabla) se mantiene junta; si no cabe, toda la sección pasa a la siguiente página.

---

## [18.0.1.8.0] - 2025-03-19

### Añadido

- **Logo y nombre de empresa** en la primera hoja del reporte (encima de "Resumen: WAVE/xxx").

### Cambiado

- **Columna Producto**: El código interno se muestra una sola vez (antes aparecía duplicado).
- **Columna Código de barras**: Renombrada a "Codigo Prod." y reducido su ancho (12%) para dar más espacio a BULTO (18%).

---

## [18.0.1.7.0] - 2025-03

### Añadido

- **Columna BULTO**: Muestra cantidad en bultos (ej. "1.5 Bulto x40") para que el recolector sepa cuántas cajas tomar. Usa `uom_po_id`, `packaging_ids` o UdM de bulto en la categoría del producto.

### Corregido

- `KeyError: 'bulto_name'` mediante `setdefault` en el modelo y `line.get()` en el template.
- Fallback a `move_ids` cuando `move_line_ids` está vacío (pickings sin "Comprobar disponibilidad").

---

## [18.0.1.2.0] - 2025-03

### Corregido

- Secuencia en tabla de traslados (1, 2, 3... en lugar de 0, 1, 2...).
- Fallback a `move_ids` para generar "Productos Consolidados" cuando no hay operaciones detalladas.

---

## [18.0.1.1.0] - 2025-03

### Añadido

- Códigos de barras embebidos como imágenes base64 para correcta renderización en PDF.

### Cambiado

- Dependencia: `python-barcode[images]` para generación de códigos de barras.

---

## [18.0.1.0.0] - 2025-03

### Añadido

- Reporte consolidado de lotes de transferencias (stock.picking.batch).
- Agrupación por producto, lote, paquete y ubicaciones.
- Compatibilidad con waves, lotes y picking multi-ubicación.

---

[18.0.1.9.0]: https://github.com/FW-CORP/nakel_picking/compare/v18.0.1.8.0...v18.0.1.9.0
[18.0.1.8.0]: https://github.com/FW-CORP/nakel_picking/compare/v18.0.1.7.0...v18.0.1.8.0
[18.0.1.7.0]: https://github.com/FW-CORP/nakel_picking/compare/v18.0.1.2.0...v18.0.1.7.0
[18.0.1.2.0]: https://github.com/FW-CORP/nakel_picking/compare/v18.0.1.1.0...v18.0.1.2.0
[18.0.1.1.0]: https://github.com/FW-CORP/nakel_picking/compare/v18.0.1.0.0...v18.0.1.1.0
[18.0.1.0.0]: https://github.com/FW-CORP/nakel_picking/releases/tag/v18.0.1.0.0
