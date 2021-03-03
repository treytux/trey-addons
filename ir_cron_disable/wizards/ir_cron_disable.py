###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class IrCronDisable(models.TransientModel):
    _name = 'ir.cron.disable'
    _description = 'Wizard for disable planned actions'

    def accept_action(self):
        for cron in self.env['ir.cron'].browse(
                self._context.get('active_ids', [])):
            cron.active = False
