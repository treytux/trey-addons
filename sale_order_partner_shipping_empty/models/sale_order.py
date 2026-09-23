###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        group = (
            'sale_order_partner_shipping_empty.group_sale_no_default_shipping')
        if self.env.user.has_group(group):
            self.partner_shipping_id = False
        return res
