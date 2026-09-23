###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agents_name = fields.Char(
        string='Agents',
        compute='_compute_agents_name',
        store=True,
    )

    @api.depends(
        'order_line.agent_ids',
        'order_line.agent_ids.agent_id',
        'order_line.agent_ids.agent_id.name'
    )
    def _compute_agents_name(self):
        for order in self:
            agent_names = {
                agent.agent_id.name
                for line in order.order_line
                for agent in line.agent_ids
                if agent.agent_id.name
            }
            order.agents_name = ', '.join(agent_names)
