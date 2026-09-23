###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountMoveAgentAssignment(models.TransientModel):
    _name = 'account.move.agent.assignment'
    _description = 'Wizard account move for agent assignment'

    agents = fields.Many2many(
        comodel_name='res.partner',
        relation='agent2move_agent_assignment',
        column1='move_agent_assignment_id',
        column2='agent_id',
        domain='[("agent", "=", True)]',
    )

    def button_accept(self):
        self.ensure_one()
        invoice_ids = self.env.context.get('active_ids', [])
        invoice_line_agent_obj = self.env['account.invoice.line.agent']
        for order in self.env['account.move'].browse(invoice_ids):
            for line in order.invoice_line_ids:
                line.agent_ids = [(6, 0, [])]
                for agent in self.agents:
                    line_agent = invoice_line_agent_obj.create({
                        'object_id': line.id,
                        'agent_id': agent.id,
                        'commission_id': agent.commission_id.id,
                    })
                    line.agent_ids = [(4, line_agent.id)]
        return {'type': 'ir.actions.act_window_close'}
