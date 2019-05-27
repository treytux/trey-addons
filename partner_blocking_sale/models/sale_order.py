###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.allowed is False:
            raise UserError(_(
                'The partner "%s" is blocked, you can not create an order '
                'for this customer') % self.partner_id.name)
        super().onchange_partner_id()
