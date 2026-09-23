###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class TimesheetsAnalysisReport(models.Model):
    _inherit = "timesheets.analysis.report"

    sheet_id = fields.Many2one(
        string="Sheet",
        comodel_name="hr_timesheet.sheet",
        readonly=True,
    )
    sheet_state = fields.Selection(
        selection=[
            ("new", "New"),
            ("draft", "Open"),
            ("confirm", "Waiting Review"),
            ("done", "Approved"),
        ],
        default="new",
        string="Status",
        readonly=True,
    )
    billable_project = fields.Boolean(
        string='Billable project',
    )

    @api.model
    def _select(self):
        select = super()._select()
        select += """
            , A.sheet_id as sheet_id
            , A.sheet_state as sheet_state
            , P.allow_billable AS billable_project
        """
        return select

    @api.model
    def _from(self):
        return super()._from() + """
        LEFT JOIN project_project P ON A.project_id = P.id"""
