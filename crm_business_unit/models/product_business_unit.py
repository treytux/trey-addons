###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models


class ProductBusinessUnit(models.Model):
    _inherit = 'product.business.unit'

    lead_ids = fields.Many2many(
        comodel_name='crm.lead',
        relation='productbusinessunit2crm',
        column1='unit_id',
        column2='lead_id',
    )
    lead_count = fields.Integer(
        compute='_compute_lead',
        string='Oportunity count',
    )
    lead_amount = fields.Float(
        compute='_compute_lead',
        string='Oportunity Revenues',
        readonly=True,
    )
    dashboard_graph_model = fields.Selection(
        selection_add=[('crm.lead', 'Lead')],
    )

    @api.depends('lead_ids')
    def _compute_lead(self):
        for unit in self:
            unit.lead_count = len(unit.lead_ids)
            unit.lead_amount = sum(unit.lead_ids.mapped('planned_revenue'))

    @api.multi
    def action_view_leads(self):
        action = self.env.ref('crm.crm_lead_opportunities_tree_view').read()[0]
        if self.lead_count:
            action['domain'] = [('id', 'in', self.lead_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _graph_date_column(self):
        if self.dashboard_graph_model == 'crm.lead':
            return 'date_deadline'
        return super()._graph_date_column()

    def _graph_y_query(self):
        if self.dashboard_graph_model == 'crm.lead':
            return 'SUM(expected_revenue)'
        return super()._graph_y_query()

    def _graph_title_and_key(self):
        if self.dashboard_graph_model == 'crm.lead':
            return ['', _('CRM: Expected Revenue')]
        return super()._graph_title_and_key()
