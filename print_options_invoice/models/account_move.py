###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_print_options_invoice(self):
        wiz = self.env['wiz.print.options.invoice'].create({})
        return {
            'name': _('Print'),
            'type': 'ir.actions.act_window',
            'res_model': 'wiz.print.options.invoice',
            'view_mode': 'form',
            'res_id': wiz.id,
            'target': 'new',
        }
