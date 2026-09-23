###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    agents_name = fields.Char(
        string='Agents',
        compute='_compute_agents_name',
        store=True,
    )

    @api.depends(
        'invoice_line_ids.agent_ids',
        'invoice_line_ids.agent_ids.agent_id',
        'invoice_line_ids.agent_ids.agent_id.name'
    )
    def _compute_agents_name(self):
        for move in self:
            agent_names = {
                agent.agent_id.name
                for line in move.invoice_line_ids
                for agent in line.agent_ids
                if agent.agent_id.name
            }
            move.agents_name = ', '.join(agent_names)
