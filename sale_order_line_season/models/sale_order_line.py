###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
    )

    @api.onchange('product_id')
    def product_id_change(self):
        res = super().product_id_change()
        if not self.product_id:
            return res
        self.season_id = (
            self.product_id and self.product_id.season_id or False)
        return res

    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = super()._prepare_invoice_line(qty)
        res['season_id'] = self.season_id.id
        return res
