###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            if sale.picking_ids:
                sale.picking_ids.write({'delivery_note': sale.delivery_message})
        return res
