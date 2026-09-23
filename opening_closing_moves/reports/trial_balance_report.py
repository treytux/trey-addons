###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ReportTrialBalance(models.TransientModel):
    _inherit = 'report_trial_balance'

    move_type = fields.Selection(
        selection=[
            ('opening', 'Opening'),
            ('closing', 'Closing'),
        ],
        default='opening',
    )

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type in ['opening', 'closing']:
            report_name = 'o_c.report_opening_closing_xlsx'
        else:
            return super().print_report(report_type)
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', 'xlsx')],
            limit=1).report_action(self, config=False)
