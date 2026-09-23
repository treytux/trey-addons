###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrderLinesByRef(models.TransientModel):
    _inherit = 'sale.order.lines_by_ref'

    def _get_product_by_ref(self, default_code):
        products = self.env['product.product'].search([
            ('sale_ok', '=', True),
            '|',
            ('default_code', '=', default_code),
            ('barcode', '=', default_code),
        ])
        if products:
            return products
        line = self.env['product.catalog.line'].search([
            ('state', '!=', 'active'),
            '|',
            ('ean', '=', default_code),
            '|',
            ('product_code', '=', default_code),
            ('default_code', '=', default_code),
        ], limit=1)
        if line:
            line.sudo().action_activate()
            if line.product_id and line.product_id.sale_ok:
                return line.product_id
        return super()._get_product_by_ref(default_code)
