###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def open_discount_wizard(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(
                    'Discounts can be modified in draft state only.'
                )
        return {
            'name': 'Modify lines discount',
            'type': 'ir.actions.act_window',
            'res_model': 'change.purchase.discount.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }
