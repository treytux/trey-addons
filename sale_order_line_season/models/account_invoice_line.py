###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super()._onchange_product_id()
        if not self.product_id:
            return res
        self.season_id = (
            self.product_id and self.product_id.season_id or False)
        return res
