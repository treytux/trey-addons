###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_send_confirmation_email(self):
        self.ensure_one()
        res = super().action_send_confirmation_email()
        commercial_partner_id = self.partner_id.commercial_partner_id
        if commercial_partner_id.delivery_slip_type == 'not_valued':
            return res
        res['context']['default_template_id'] = self.env.ref(
            'print_formats_picking.mail_delivery_valued_confirmation').id
        return res
