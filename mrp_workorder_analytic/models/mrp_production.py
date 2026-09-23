###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    analytic_line_ids = fields.One2many(
        comodel_name='account.analytic.line',
        compute='_compute_analytic_line_ids',
        string='Analytic Lines',
    )
    analytic_line_count = fields.Integer(
        compute='_compute_analytic_line_ids',
    )

    @api.multi
    def write(self, values):
        res = super().write(values)
        for production in self.filtered(
                lambda p: p.analytic_account_id and p.workorder_ids):
            production.workorder_ids._create_analytic_line()
        return res

    @api.depends('workorder_ids.time_ids.analytic_line_id')
    def _compute_analytic_line_ids(self):
        for production in self:
            production.analytic_line_ids = (
                production.workorder_ids.time_ids.mapped('analytic_line_id'))
            production.analytic_line_count = len(production.analytic_line_ids)

    @api.multi
    def action_view_analytic_lines(self):
        self.ensure_one()
        action = self.env.ref(
            'analytic.account_analytic_line_action').read()[0]
        action['domain'] = [
            ('id', 'in', self.analytic_line_ids.ids)]
        return action
