###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    opening_closing_move = fields.Boolean(
        string="Opening/Closing Move",
    )
    move_type = fields.Selection(
        selection=[
            ("opening", "Opening"),
            ("closing", "Closing"),
        ],
        default="closing",
    )

    def button_create_move(self):
        self.ensure_one()
        return self._export(self.move_type)

    @api.onchange("opening_closing_move")
    def _onchange_opening_closing_move(self):
        if self.opening_closing_move:
            self.show_hierarchy = False
            self.hide_account_at_0 = True
            self.show_partner_details = False
            self.limit_hierarchy_level = False
            self.hide_parent_hierarchy_level = False
            self.foreign_currency = False
            self.journal_ids = False
            self.account_ids = False
            self.receivable_accounts_only = False
            self.payable_accounts_only = False
            self.grouped_by = False

    def _prepare_report_data(self):
        self.ensure_one()
        values = super()._prepare_report_data()
        values.update({"move_type": self.move_type})
        return values

    def _print_report(self, report_type):
        self.ensure_one()
        if report_type not in ["opening", "closing"]:
            return super()._print_report(report_type)
        data = self._prepare_report_data()
        report_name = "o_c.report_opening_closing_xlsx"
        return (
            self.env["ir.actions.report"]
            .search(
                [
                    ("report_name", "=", report_name),
                    ("report_type", "=", "xlsx"),
                ],
                limit=1,
            )
            .report_action(self, data=data)
        )
