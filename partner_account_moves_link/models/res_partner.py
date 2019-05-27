###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, api
from ast import literal_eval


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def action_view_account_move_lines(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_a').read()[0]
        action['domain'] = (
            action['domain'] and literal_eval(action['domain']) or [])
        action['domain'].append(('partner_id', 'child_of', self.id))
        return action
