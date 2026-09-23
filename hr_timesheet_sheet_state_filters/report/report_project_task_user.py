###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ReportProjectTaskUser(models.Model):
    _inherit = "report.project.task.user"

    hours_effective_pending = fields.Float(
        string='Hours effective pending',
        readonly=True,
    )
    hours_effective_approve = fields.Float(
        string='Hours effective approve',
        store=True,
    )

    def _select(self):
        select = super()._select()
        select += """
            , t.effective_hours_pending as hours_effective_pending
            , t.effective_hours_approve as hours_effective_approve
        """
        return select

    def _group_by(self):
        res = super()._group_by()
        res += """
            , t.effective_hours_pending
            , t.effective_hours_approve
        """
        return res
