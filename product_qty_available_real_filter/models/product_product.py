###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_real = fields.Float(
        search='_search_qty_available_real',
    )

    @api.model
    def _search_qty_available_real(self, operator, value):
        if (value == 0.0 and operator == '>' and not (
                {'from_date', 'to_date'} & set(self.env.context.keys()))):
            product_ids = self._search_qty_available_real_new(
                self.env.context.get('lot_id'),
                self.env.context.get('owner_id'),
                self.env.context.get('package_id'))
            return [('id', 'in', product_ids)]
        return self._search_product_quantity(operator, value, 'qty_available')

    def _search_qty_available_real_new(
            self, lot_id=False, owner_id=False, package_id=False):
        product_ids = set()
        domain_quant = self._get_domain_locations()[0]
        if lot_id:
            domain_quant.append(('lot_id', '=', lot_id))
        if owner_id:
            domain_quant.append(('owner_id', '=', owner_id))
        if package_id:
            domain_quant.append(('package_id', '=', package_id))
        quants_groupby = self.env['stock.quant'].read_group(
            domain_quant, ['product_id', 'quantity'], ['product_id'],
            orderby='id')
        for quant in quants_groupby:
            product_obj = self.env['product.product']
            product = product_obj.browse(quant['product_id'][0])
            qty_real = quant['quantity'] - product.outgoing_qty
            if qty_real > 0 and product.outgoing_qty < qty_real:
                product_ids.add(quant['product_id'][0])
        return list(product_ids)
