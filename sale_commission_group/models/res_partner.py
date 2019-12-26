###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    agents_name = fields.Char(
        string='Agents',
        compute='_compute_agents_name',
        store=True)
    customers_count = fields.Integer(
        compute='_compute_customers',
        string='Customers count')
    agent_customers = fields.Many2many(
        compute='_compute_agent_customers',
        string='Agent Customers',
        comodel_name='res.partner',
        relation='agent2customers_rel',
        column1='agent_id',
        column2='customer_id')

    @api.one
    @api.depends('agents')
    def _compute_agents_name(self):
        self.agents_name = ', '.join(
            list(set([ag.name for ag in self.agents])))

    @api.multi
    def _get_customers_domain(self):
        return [('is_company', '=', True), ('agents', 'in', self.ids)]

    @api.multi
    @api.depends('agent_customers')
    def _compute_customers(self):
        for agent in self:
            agent.customers_count = len(agent.agent_customers)

    @api.multi
    @api.depends('agents')
    def _compute_agent_customers(self):
        for agent in self:
            agent_customers = self.env['res.partner'].search(
                self._get_customers_domain(), order='name ASC')
            if agent_customers:
                self.agent_customers = [(6, 0, agent_customers.ids)]

    @api.multi
    def action_view_customers(self):
        form_view = self.env.ref('base.view_partner_form')
        tree_view = self.env.ref('base.view_partner_tree')
        search_view = self.env.ref('base.view_res_partner_filter')
        return {
            'name': _('Associated customers'),
            'domain': self._get_customers_domain(),
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'view_mode': 'tree,form',
            'search_view_id': search_view.id,
            'view_type': 'form'}
