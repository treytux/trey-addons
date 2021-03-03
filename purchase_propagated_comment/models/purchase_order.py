###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_propagated_comment = fields.Text(
        string='Purchase Propagated Comment',
    )

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if not self.partner_id:
            return res
        self.purchase_propagated_comment = (
            self.partner_id.purchase_propagated_comment)
        return res
