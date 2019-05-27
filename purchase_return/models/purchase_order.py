###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_return = fields.Boolean(
        string='Is Return',
        compute='_compute_is_return')

    @api.one
    @api.depends('amount_total')
    def _compute_is_return(self):
        self.is_return = self.amount_total < 0

    @api.multi
    def _add_supplier_to_product(self):
        if self.is_return:
            return
        return super()._add_supplier_to_product()
