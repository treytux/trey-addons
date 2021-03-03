###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_print_picking_valued(self):
        commercial_partner_id = self.partner_id.commercial_partner_id
        if commercial_partner_id.delivery_slip_type == 'valued':
            return self.env.ref(
                'print_formats_picking_valued.'
                'report_stock_deliveryslip_valued_create'
            ).report_action(self)
        else:
            return self.env.ref(
                'stock.action_report_delivery'
            ).report_action(self)
