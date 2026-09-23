###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
        compute='_compute_purchase_propagated_comment',
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends('partner_id')
    def _compute_purchase_propagated_comment(self):
        for order in self:
            order.purchase_propagated_comment = (
                order.partner_id.purchase_propagated_comment)
