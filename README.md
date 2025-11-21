# Nakel Picking - Consolidated Batch Report

## Descripción

Este módulo para Odoo 18 modifica la impresión de lotes de transferencias (stock.picking.batch) para consolidar las cantidades de productos, agrupándolas de manera inteligente.

## Características

- **Consolidación Detallada**: Agrupa productos por:
  - Producto
  - Lote/Número de Serie
  - Paquete origen y destino
  - Ubicación origen
  - Ubicación destino

- **Resumen Simplificado**: Vista alternativa que consolida solo por producto

- **Compatible con**:
  - Seguimiento por lotes
  - Paquetes
  - Olas (waves)
  - Preparación de múltiples órdenes
  - Picking multi ubicación

## Requisitos

Este módulo requiere la biblioteca Python `python-barcode` para generar códigos de barras en reportes PDF:

```bash
# Instalar usando pip (dentro del entorno virtual de Odoo)
pip install python-barcode[images]

# O instalar usando requirements.txt
pip install -r requirements.txt
```

Si `python-barcode` no está disponible, el módulo intentará usar `reportlab` como alternativa (generalmente ya incluida en Odoo).

## Instalación

1. Instala las dependencias Python requeridas (ver sección Requisitos)
2. Copia este módulo en tu directorio de addons de Odoo
3. Actualiza la lista de aplicaciones
4. Busca "Nakel Picking - Consolidated Batch Report"
5. Instala el módulo

## Uso

Una vez instalado el módulo, **el reporte estándar de lotes se reemplaza automáticamente** con la versión consolidada. No necesitas seleccionar ningún reporte especial.

### Reporte Consolidado (Reemplazo Automático)

Este reporte muestra:

**Página 1: Lista de Traslados**
- Encabezado con nombre del lote y código de barras
- Responsable y estado del lote
- Tabla con todos los traslados incluidos (con códigos de barras individuales)

**Página 2+: Productos Consolidados**
- Productos agrupados por ruta (DESDE ubicación A ubicación destino)
- Tabla consolidada con:
  - Producto (código y nombre)
  - Cantidad consolidada
  - Traslados que contribuyen a esa cantidad
  - Código de barras del producto
  - Paquete (origen → destino si aplica)

## Cómo acceder al reporte

1. Ve a **Inventario > Operaciones > Lotes/Olas**
2. Abre un lote de transferencias
3. Haz clic en el botón **Imprimir**
4. El reporte consolidado se genera automáticamente (reemplaza el reporte estándar)

## Ejemplo de uso

**Escenario**: Tienes un lote con 3 transferencias que incluyen:
- CEN/PICK/00001: ROCHER (5 unidades), de CEN/Existencias → CEN/Salida
- CEN/PICK/00022: ROCHER (5 unidades), de CEN/Existencias → CEN/Salida
- CEN/PICK/00060: ROCHER (1 unidad), de CEN/Existencias → CEN/Salida
- CEN/PICK/00059: ROCHER (1 unidad), de CEN/Existencias → CEN/Salida

**Sin el módulo (reporte estándar):**
Mostraría 4 líneas separadas con ROCHER (5.0, 5.0, 1.0, 1.0)

**Con el módulo (reporte consolidado):**
Muestra una sola línea:
```
DESDE CEN/Existencias
A CEN/Salida

[1244.90] ROCHER X3U.-434 (16)  |  12.00 Unidades  |  CEN/PICK/00001, CEN/PICK/00022, CEN/PICK/00060, CEN/PICK/00059
```

## Estructura técnica

```
nakel_picking/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── stock_picking_batch.py
└── reports/
    └── stock_picking_batch_report.xml
```

### Métodos principales

**`_get_consolidated_lines()`**: Consolida líneas agrupando por producto, lote, paquete y ubicaciones.

**`_get_consolidated_lines_by_product()`**: Consolida solo por producto (para resumen simple).

**`_generate_barcode_image(value, barcode_type, width, height)`**: Genera imágenes de códigos de barras como base64 para embeber en reportes PDF. Esto resuelve problemas de renderización de códigos de barras en PDFs generados por wkhtmltopdf.

## Solución a problemas de códigos de barras

En versiones anteriores, los códigos de barras podían aparecer como pequeños iconos o no renderizarse correctamente en los PDFs. Esto se debía a que wkhtmltopdf (el motor de renderizado de PDFs de Odoo) tenía problemas accediendo a la URL `/report/barcode/`.

**Solución implementada**: Los códigos de barras ahora se generan como imágenes base64 embebidas directamente en el HTML del reporte, garantizando su correcta visualización en PDFs sin depender de URLs externas.

## Licencia

LGPL-3

## Autor

s.paradiso92@gmail.com

## Versión

18.0.1.0.0
