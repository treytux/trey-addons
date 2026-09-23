###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    use_planned_revenue = fields.Boolean(
        string='Set planned revenue target',
        help="Check this box to set a planning revenue target.")
    planned_revenue = fields.Integer(
        compute='_compute_planned_revenue',
        string='Opportunities planned revenue',
        readonly=True,
        help="Planned revenue for opportunities.")
    planned_revenue_target = fields.Integer(
        string='Planning revenue Target',
        help="Target of planned revenue for the current opportunities.")

    def _compute_planned_revenue(self):
        for team in self:
            leads = self.env['crm.lead'].search([
                ('team_id', '=', team.id),
                ('probability', '<', 100),
                ('type', '=', 'opportunity'),
            ])
            for lead in leads:
                team.planned_revenue += (lead.planned_revenue
                                         * (lead.probability / 100))

    def update_planned_revenue_target(self, value):
        return self.write({'planned_revenue_target': round(float(value or 0))})
