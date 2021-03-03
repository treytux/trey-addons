###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderAgentAssignment(models.TransientModel):
    _name = 'sale.order.agent.assignment'
    _description = 'Wizard sale order for agent assignment'

    agents = fields.Many2many(
        comodel_name='res.partner',
        domain="[('agent', '=', True)]",
    )

    @api.multi
    def button_accept(self):
        order_ids = self.env.context.get('active_ids', [])
        for order in self.env['sale.order'].browse(order_ids):
            for line in order.order_line:
                line.agents = [(6, 0, [])]
                for agent in self.agents:
                    line_agent = self.env['sale.order.line.agent'].create({
                        'object_id': line.id,
                        'agent': agent.id,
                        'commission': agent.commission.id,
                    })
                    line.agents = [(4, line_agent.id)]
        return {'type': 'ir.actions.act_window_close'}
