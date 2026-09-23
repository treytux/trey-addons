###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    timesheet_ids = fields.One2many(
        comodel_name='account.analytic.line',
        inverse_name='production_id',
        copy=False,
        string='Timesheets',
    )
    timesheet_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Timesheet Project',
        compute='_compute_timesheet_project_id',
    )

    def _compute_timesheet_project_id(self):
        for prdc in self:
            prdc.timesheet_project_id = self.env['project.project'].search([
                ('analytic_account_id', '=', prdc.analytic_account_id.id),
                ('allow_timesheets', '=', True),
            ], limit=1)
