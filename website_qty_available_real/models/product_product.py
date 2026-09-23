###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _search_qty_available_real_website(self, operator, value):
        if (value == 0.0 and operator == '>' and not (
                {'from_date', 'to_date'} & set(self.env.context.keys()))):
            product_ids = self._search_qty_available_real_new_website(
                self.env.context.get('lot_id'),
                self.env.context.get('owner_id'),
                self.env.context.get('package_id'))
            return [('id', 'in', product_ids)]
        return self._search_product_quantity(operator, value, 'qty_available')

    def _search_qty_available_real_new_website(
            self, lot_id=False, owner_id=False, package_id=False):
        domain_quant = self._get_domain_locations()[0]
        domain_quant.append(('product_id.is_published', '=', True))
        if lot_id:
            domain_quant.append(('lot_id', '=', lot_id))
        if owner_id:
            domain_quant.append(('owner_id', '=', owner_id))
        if package_id:
            domain_quant.append(('package_id', '=', package_id))
        quants = self.env['stock.quant'].search_read(
            domain_quant, ['product_id', 'quantity', 'reserved_quantity'],
            order='id')
        return list(set([
            quant['product_id'][0] for quant in quants if quant['quantity']
            > quant['reserved_quantity']]))
