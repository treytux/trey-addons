###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_state = fields.Char(
        string='Product State',
    )

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        if not self.product_id:
            return res
        self.product_state = self.product_id.product_tmpl_id.state or False
        return res
