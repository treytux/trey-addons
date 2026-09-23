###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class EventEvent(models.Model):
    _inherit = 'event.event'

    def action_scan_tickets_barcodes(self):
        self.ensure_one()
        view = self.env.ref(
            'event_registration_barcodes.event_registration_barcodes_wizard')
        wizard = self.env['event.registration.barcodes'].create({
            'event_id': self.id,
        })
        context = self.env.context.copy()
        context['wizard_id'] = wizard.id
        self.env.context = context
        return {
            'name': _('Scan tickets'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'event.registration.barcodes',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wizard.id,
            'context': self.env.context,
        }
