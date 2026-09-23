###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class QCReport(models.TransientModel):
    _name = 'qc.report'
    _description = 'Quality Control Report'

    def _get_default_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(qc_report)')])
        if not reports.exists():
            return None
        return reports[0]

    def _get_domain_report(self):
        reports = self.env['ir.actions.report'].with_context(
            lang='en_US').search([('name', 'ilike', '(qc_report)')])
        return [('id', 'in', reports and reports.ids or [0])]

    report_id = fields.Many2one(
        comodel_name='ir.actions.report',
        string='Report',
        domain=_get_domain_report,
        default=lambda self: self._get_default_report(),
        required=True,
    )

    def action_print(self):
        model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        docs = self.env[model].browse(active_ids)
        return self.env.ref(self.report_id.xml_id).report_action(docs)
