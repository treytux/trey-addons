###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    delivery_note = fields.Text(
        string='Information for carrier',
    )

    @api.multi
    def action_confirm(self):
        res = super().action_confirm()
        for sale in self:
            if sale.picking_ids:
                sale.picking_ids.write({'delivery_note': sale.delivery_note})
        return res
