###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class AccountInvoiceAgentAssignment(models.TransientModel):
    _name = 'account.invoice.agent.assignment'
    _description = 'Wizard account invoice for agent assignment'

    agents = fields.Many2many(
        comodel_name='res.partner',
        domain="[('agent', '=', True)]",
    )

    @api.multi
    def button_accept(self):
        order_ids = self.env.context.get('active_ids', [])
        invoice_line_agent_obj = self.env['account.invoice.line.agent']
        for order in self.env['account.invoice'].browse(order_ids):
            for line in order.invoice_line_ids:
                line.agents = [(6, 0, [])]
                for agent in self.agents:
                    line_agent = invoice_line_agent_obj.create({
                        'object_id': line.id,
                        'agent': agent.id,
                        'commission': agent.commission.id,
                    })
                    line.agents = [(4, line_agent.id)]
        return {'type': 'ir.actions.act_window_close'}
