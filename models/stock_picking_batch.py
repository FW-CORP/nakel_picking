# -*- coding: utf-8 -*-

from odoo import models, fields, api
from collections import defaultdict
import base64
import io


class StockPickingBatch(models.Model):
    _inherit = 'stock.picking.batch'

    def _get_consolidated_lines(self):
        """
        Consolidates move lines from all pickings in the batch.
        Groups by product, lot, package, source location and destination location.
        Returns a list of consolidated line dictionaries.

        Uses move_line_ids when available (detailed operations).
        Falls back to move_ids when move_line_ids is empty (e.g. pickings not yet checked).
        """
        self.ensure_one()

        # Dictionary to accumulate quantities
        # Key: (product_id, lot_id, package_id, location_id, location_dest_id)
        consolidated = defaultdict(lambda: {
            'product': None,
            'product_name': '',
            'product_code': '',
            'lot': None,
            'lot_name': '',
            'package': None,
            'package_name': '',
            'result_package': None,
            'result_package_name': '',
            'bulto_name': '',  # Nombre del embalaje/bulto del producto (ej. "Caja x 12")
            'bulto_qty': 0.0,  # Cantidad por bulto
            'location': None,
            'location_name': '',
            'location_dest': None,
            'location_dest_name': '',
            'quantity': 0.0,
            'uom': None,
            'uom_name': '',
            'picking_ids': [],
            'picking_names': [],
        })

        # Iterate through all pickings in the batch
        for picking in self.picking_ids:
            # Prefer move_line_ids (detailed operations); fallback to move_ids if empty
            lines_to_process = list(picking.move_line_ids) if picking.move_line_ids else []

            if not lines_to_process:
                # Fallback: use move_ids when move_line_ids is empty (pickings not yet checked)
                for move in picking.move_ids:
                    if not move.product_uom_qty:
                        continue
                    # Build pseudo move_line from move (no lot/package info until operations exist)
                    pseudo = type('PseudoMoveLine', (), {
                        'product_id': move.product_id,
                        'lot_id': None,
                        'package_id': None,
                        'result_package_id': None,
                        'location_id': move.location_id,
                        'location_dest_id': move.location_dest_id,
                        'quantity': move.product_uom_qty,
                        'product_uom_id': move.product_uom,
                    })()
                    lines_to_process.append(pseudo)

            for move_line in lines_to_process:
                # Skip lines without quantity
                if not move_line.quantity:
                    continue

                # Create the grouping key
                key = (
                    move_line.product_id.id,
                    move_line.lot_id.id if move_line.lot_id else False,
                    move_line.package_id.id if move_line.package_id else False,
                    move_line.location_id.id,
                    move_line.location_dest_id.id,
                )

                # Initialize or update the consolidated data
                if consolidated[key]['product'] is None:
                    product = move_line.product_id
                    line_uom = move_line.product_uom_id
                    # Calcular bultos: cantidad en UdM de bulto (ej. "Bulto x40") para que el recolector
                    # sepa cuántas cajas/bultos cerrados tomar sin contar unidades sueltas
                    bulto_name = ''
                    bulto_qty = 0.0

                    # Buscar UdM de bulto: uom_po_id (compra) o packaging - para que recolector
                    # sepa cuántas cajas cerradas tomar sin abrirlas para contar unidades
                    bulto_uom = None
                    units_per_bulto = 0.0
                    qty_already_in_bultos = False  # True si quantity está en bultos (no en unidades)
                    if product.product_tmpl_id:
                        pt = product.product_tmpl_id
                        line_uom = move_line.product_uom_id
                        # Si la línea ya está en UdM de bulto (ej. Bulto x40), quantity ya son bultos
                        try:
                            uom_factor = getattr(line_uom, 'factor_inv', 1) or 1
                            if uom_factor > 1:
                                bulto_name = line_uom.name or ''
                                qty_already_in_bultos = True
                                units_per_bulto = 1  # Para que bulto_qty = quantity en post-proc
                        except Exception:
                            pass
                        # Si no: buscar uom_po_id (UdM compra, ej. "Bulto x40")
                        if not bulto_name and pt.uom_po_id and pt.uom_po_id != pt.uom_id:
                            try:
                                units_per_bulto = getattr(pt.uom_po_id, 'factor_inv', 0) or 0
                                if units_per_bulto > 1:
                                    bulto_uom = pt.uom_po_id
                                    bulto_name = bulto_uom.name or ''
                            except Exception:
                                pass
                        # Fallback: uom_id del producto si ya es bulto (ej. producto vendido por bulto)
                        if not bulto_name and pt.uom_id:
                            try:
                                uom_factor = getattr(pt.uom_id, 'factor_inv', 0) or 0
                                if uom_factor > 1:
                                    bulto_name = pt.uom_id.name or ''
                                    units_per_bulto = uom_factor
                            except Exception:
                                pass
                        # Fallback: packaging (ej. "Caja x 12")
                        if not bulto_name and pt.packaging_ids:
                            pkg = pt.packaging_ids[0]
                            units_per_bulto = pkg.qty or 0
                            if units_per_bulto > 0:
                                bulto_name = pkg.name or ('x %.0f' % units_per_bulto)
                        # Fallback: buscar UdM tipo bulto en la categoría del producto
                        if not bulto_name and pt.uom_id and pt.uom_id.category_id:
                            try:
                                bulto_uom_cat = self.env['uom.uom'].search([
                                    ('category_id', '=', pt.uom_id.category_id.id),
                                    ('factor_inv', '>', 1)
                                ], order='factor_inv desc', limit=1)
                                if bulto_uom_cat:
                                    bulto_name = bulto_uom_cat.name or ''
                                    units_per_bulto = bulto_uom_cat.factor_inv or 0
                            except Exception:
                                pass

                    consolidated[key].update({
                        'product': product,
                        'product_name': product.display_name,
                        'product_code': product.default_code or '',
                        'lot': move_line.lot_id,
                        'lot_name': move_line.lot_id.name if move_line.lot_id else '',
                        'package': move_line.package_id,
                        'package_name': move_line.package_id.name if move_line.package_id else '',
                        'result_package': move_line.result_package_id,
                        'result_package_name': move_line.result_package_id.name if move_line.result_package_id else '',
                        'bulto_name': bulto_name,
                        'bulto_qty': bulto_qty,
                        'units_per_bulto': units_per_bulto,
                        'qty_already_in_bultos': qty_already_in_bultos,
                        'bulto_uom': bulto_uom,
                        'location': move_line.location_id,
                        'location_name': move_line.location_id.display_name,
                        'location_dest': move_line.location_dest_id,
                        'location_dest_name': move_line.location_dest_id.display_name,
                        'uom': move_line.product_uom_id,
                        'uom_name': move_line.product_uom_id.name,
                    })

                # Accumulate quantity
                consolidated[key]['quantity'] += move_line.quantity

                # Track which pickings contributed to this line
                if picking.id not in consolidated[key]['picking_ids']:
                    consolidated[key]['picking_ids'].append(picking.id)
                    consolidated[key]['picking_names'].append(picking.name)

        # Convert to sorted list y asegurar que todas las líneas tengan bulto_name/bulto_qty
        result = sorted(
            consolidated.values(),
            key=lambda x: (
                x['product_name'],
                x['lot_name'],
                x['location_name'],
                x['location_dest_name']
            )
        )
        for line in result:
            line.setdefault('bulto_name', '')
            line.setdefault('bulto_qty', 0.0)
            line.setdefault('units_per_bulto', 0.0)
            line.setdefault('qty_already_in_bultos', False)
            # Calcular cuántos bultos representa la cantidad (para el recolector)
            qty = line.get('quantity', 0)
            if line.get('qty_already_in_bultos'):
                line['bulto_qty'] = round(qty, 2)  # quantity ya está en bultos
            else:
                units_per_bulto = line.get('units_per_bulto') or 0
                if units_per_bulto > 0 and qty > 0:
                    line['bulto_qty'] = round(qty / units_per_bulto, 2)
                else:
                    line['bulto_qty'] = 0.0

        return result

    def _get_consolidated_lines_by_product(self):
        """
        Alternative consolidation: only by product (no lot/package/location detail).
        This is useful for a simple summary view.
        """
        self.ensure_one()

        consolidated = defaultdict(lambda: {
            'product': None,
            'product_name': '',
            'product_code': '',
            'quantity': 0.0,
            'uom': None,
            'uom_name': '',
        })

        for picking in self.picking_ids:
            for move_line in picking.move_line_ids:
                if not move_line.quantity:
                    continue

                key = move_line.product_id.id

                if consolidated[key]['product'] is None:
                    consolidated[key].update({
                        'product': move_line.product_id,
                        'product_name': move_line.product_id.display_name,
                        'product_code': move_line.product_id.default_code or '',
                        'uom': move_line.product_uom_id,
                        'uom_name': move_line.product_uom_id.name,
                    })

                consolidated[key]['quantity'] += move_line.quantity

        result = sorted(
            consolidated.values(),
            key=lambda x: x['product_name']
        )

        return result

    def _generate_barcode_image(self, value, barcode_type='Code128', width=600, height=100):
        """
        Generate a barcode image as base64 string for embedding in PDF reports.

        :param value: The value to encode in the barcode
        :param barcode_type: Type of barcode (default: Code128)
        :param width: Width in pixels
        :param height: Height in pixels
        :return: base64 encoded image string with data URI prefix
        """
        if not value:
            return ''

        try:
            # Try using python-barcode library
            import barcode
            from barcode.writer import ImageWriter

            # Create barcode instance
            barcode_class = barcode.get_barcode_class(barcode_type.lower())
            barcode_instance = barcode_class(str(value), writer=ImageWriter())

            # Generate barcode to BytesIO buffer (sin texto debajo para evitar deformación en PDF)
            buffer = io.BytesIO()
            opts = {
                'module_width': 0.3,
                'module_height': 10.0,
                'quiet_zone': 2.0,
                'font_size': 0,  # Suprime texto debajo (documentación python-barcode)
                'write_text': False,  # Sin número debajo - evita solapamiento
            }
            try:
                barcode_instance.write(buffer, options=opts)
            except (TypeError, KeyError):
                buffer = io.BytesIO()
                opts.pop('write_text', None)
                barcode_instance.write(buffer, options=opts)

            # Get image data and encode to base64
            buffer.seek(0)
            barcode_image = buffer.read()

            if barcode_image:
                # Convert to base64 with data URI
                return 'data:image/png;base64,' + base64.b64encode(barcode_image).decode('utf-8')

        except ImportError:
            # If python-barcode is not available, try reportlab
            try:
                from reportlab.graphics.barcode import code128
                from reportlab.lib.units import mm
                from reportlab.graphics import renderPM

                # Create barcode
                barcode_obj = code128.Code128(str(value), barHeight=15*mm, barWidth=0.8)

                # Render to image
                barcode_image = renderPM.drawToString(barcode_obj, fmt='PNG')

                if barcode_image:
                    return 'data:image/png;base64,' + base64.b64encode(barcode_image).decode('utf-8')

            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f'Error generating barcode with reportlab for value {value}: {str(e)}')

        except Exception as e:
            # Log the error but don't break the report
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f'Error generating barcode for value {value}: {str(e)}')

        return ''
