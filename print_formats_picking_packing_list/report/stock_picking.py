###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ReportPickingPackingList(models.AbstractModel):
    _name = 'report.print_formats_picking_packing_list.report_packing_list'
    _description = 'Packing List Report Parser'

    @api.model
    def _get_product_sort_key(self, product):
        return (
            product.default_code or '', product.display_name or '', product.id)

    @api.model
    def _get_product_weight_volume_in_standard_uom(
            self, product, kg_uom, litre_uom):
        weight_uom = product.weight_uom_id or kg_uom
        volume_uom = product.volume_uom_id or litre_uom
        return (
            weight_uom._compute_quantity(
                product.weight or 0.0, kg_uom, round=False),
            volume_uom._compute_quantity(
                product.volume or 0.0, litre_uom, round=False) / 1000.0)

    @api.model
    def _get_product_package_lines(self, packages):
        kg_uom = self.env.ref('uom.product_uom_kgm')
        litre_uom = self.env.ref('uom.product_uom_litre')
        product_values = {}
        for package in packages.sorted(lambda p: (p.name or '', p.id)):
            box_type = package.dummy_id.packaging_id
            package_products = {}
            for quant in package.quant_ids:
                product = quant.product_id
                unit_weight, unit_volume = (
                    self._get_product_weight_volume_in_standard_uom(
                        product, kg_uom, litre_uom))
                if product.id not in package_products:
                    package_products[product.id] = {
                        'product': product,
                        'quantity': 0.0,
                        'weight': 0.0,
                        'volume': 0.0,
                    }
                package_product = package_products[product.id]
                package_product['quantity'] += quant.quantity
                package_product['weight'] += quant.quantity * unit_weight
                package_product['volume'] += quant.quantity * unit_volume
            for product_id, package_product in package_products.items():
                if product_id not in product_values:
                    product_values[product_id] = {
                        'product': package_product['product'],
                        'box_types': set(),
                        'box_count': 0,
                        'quantity': 0.0,
                        'weight': 0.0,
                        'volume': 0.0,
                    }
                product_line = product_values[product_id]
                product_line['box_types'].add(box_type.display_name or '-')
                product_line['box_count'] += 1
                product_line['quantity'] += package_product['quantity']
                product_line['weight'] += package_product['weight']
                product_line['volume'] += package_product['volume']
        lines = []
        for product_line in sorted(
                product_values.values(),
                key=lambda line: self._get_product_sort_key(line['product'])):
            product_line['box_type'] = ', '.join(
                sorted(product_line.pop('box_types')))
            product_line['quantity'] = round(product_line['quantity'], 2)
            product_line['weight'] = round(product_line['weight'], 2)
            product_line['volume'] = round(product_line['volume'], 4)
            lines.append(product_line)
        return lines

    def _get_packing_list_data(self, pickings):
        packages = pickings.mapped('package_ids')
        product_lines = self._get_product_package_lines(packages)
        return {
            'picking_names': ', '.join(pickings.mapped('name')),
            'package_count': len(packages),
            'product_lines': product_lines,
            'totals': {
                'weight': round(sum(
                    product_line['weight']
                    for product_line in product_lines), 2),
                'volume': round(sum(
                    product_line['volume']
                    for product_line in product_lines), 4),
            },
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': docs,
            'get_packing_list_data': self._get_packing_list_data,
        }
