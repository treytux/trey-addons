###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    agents_name = fields.Char(
        string='Agents',
        compute='_compute_agents_name',
        store=True)

    @api.one
    @api.depends('invoice_line_ids.agents')
    def _compute_agents_name(self):
        agent_list = [
            ag.agent.name for line in self.invoice_line_ids
            for ag in line.agents]
        self.agents_name = ', '.join(list(set(agent_list)))
