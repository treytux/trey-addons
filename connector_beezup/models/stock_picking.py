###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        res = super().action_done()
        for picking in self:
            if (not picking.carrier_tracking_ref
                    or not picking.sale_id
                    or not picking.sale_id.from_import_sale_beezup):
                continue
            self.env['beezup.api'].sync_beezup_order_state(picking)
        return res
