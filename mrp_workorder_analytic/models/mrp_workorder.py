###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    analytic_line_ids = fields.One2many(
        comodel_name='account.analytic.line',
        compute='_compute_analytic_line_ids',
        string='Analytic Lines',
    )
    analytic_line_count = fields.Integer(
        compute='_compute_analytic_line_ids',
    )

    @api.multi
    def _create_analytic_line(self):
        for workorder in self.filtered(lambda w: w.state == 'done'):
            if workorder.production_id.analytic_account_id:
                for time in workorder.time_ids.filtered(
                        lambda line: not line.analytic_line_id):
                    time._create_analytic_line()

    @api.depends('time_ids.analytic_line_id')
    def _compute_analytic_line_ids(self):
        for workorder in self:
            workorder.analytic_line_ids = (
                workorder.time_ids.mapped('analytic_line_id'))
            workorder.analytic_line_count = len(workorder.analytic_line_ids)

    @api.multi
    def action_view_analytic_lines(self):
        self.ensure_one()
        action = self.env.ref(
            'analytic.account_analytic_line_action').read()[0]
        action['domain'] = [
            ('id', 'in', self.analytic_line_ids.ids)]
        return action

    @api.multi
    def record_production(self):
        res = super().record_production()
        self._create_analytic_line()
        return res
