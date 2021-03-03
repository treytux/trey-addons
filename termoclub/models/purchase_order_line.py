###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, exceptions, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def action_termoclub_check_stock(self):
        self.ensure_one()
        if not self.product_id or not self.product_id.is_termoclub:
            return
        message = self.product_id.termoclub_check_stock()
        raise exceptions.UserError(_(message))
