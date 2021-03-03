###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_open_quants(self):
        products = self.mapped('product_variant_ids')
        do_popover = self.env['ir.config_parameter'].sudo().get_param(
            'sale_stock_quant_available.sale_stock_popover',
            'False').lower() == 'true'
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['name'] = _('Stock On Hand of: %s' % self.name)
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {
            'search_default_internal_loc': 1,
            'search_default_locationgroup': 1,
        }
        if do_popover:
            action['target'] = 'new'
        return action
