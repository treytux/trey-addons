###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models


class ContractLiteContract(models.Model):
    _inherit = 'contract_lite.contract'

    def action_open_server_occupation_import_wizard(self):
        active_ids = self.ids or self.env.context.get('active_ids', [])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Customer Occupation'),
            'res_model': 'contract.lite.line.server.occupation.import.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'contract_lite_line_server.'
                'contract_lite_line_server_occupation_import_wizard_form').id,
            'target': 'new',
            'context': {
                'active_model': 'contract_lite.contract',
                'active_ids': active_ids,
                'active_id': active_ids[0] if active_ids else False,
            },
        }
