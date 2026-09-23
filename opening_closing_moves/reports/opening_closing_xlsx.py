###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero


class OpeningClosingXslx(models.AbstractModel):
    _name = "report.o_c.report_opening_closing_xlsx"
    _inherit = "report.account_financial_report.abstract_report_xlsx"

    def _get_report_name(self, report, data=False):
        if report.move_type == "opening":
            report_name = _("Opening Move")
        else:
            report_name = _("Closing Move")
        return self._get_report_complete_name(report, report_name, data=data)

    def _get_report_columns(self, report):
        return {
            0: {"header": _("Code"), "field": "code", "width": 10},
            1: {"header": _("Account"), "field": "name", "width": 60},
            2: {"header": _("Debit"), "field": "debit", "type": "amount", "width": 14},
            3: {
                "header": _("Credit"),
                "field": "credit",
                "type": "amount",
                "width": 14,
            },
        }

    def _get_report_filters(self, report):
        return []

    def _get_col_count_filter_name(self):
        return 2

    def _get_col_count_filter_value(self):
        return 2

    def _get_earning_account(self, company):
        return self.env["account.account"].search(
            [
                ("account_type", "=", "equity_unaffected"),
                ("company_id", "=", company.id),
            ]
        )

    def _line_to_debit_credit(self, value, move_type):
        if move_type == "opening":
            if value > 0:
                return abs(value), 0.0
            return 0.0, abs(value)
        if value > 0:
            return 0.0, abs(value)
        return abs(value), 0.0

    def _write_opening_closing_line(self, balance, report_data):
        code = balance.get("code", "")
        name = balance.get("name", "")
        if report_data["sheet"]:
            report_data["sheet"].write_string(report_data["row_pos"], 0, code)
            report_data["sheet"].write_string(report_data["row_pos"], 1, name)
            report_data["sheet"].write_number(
                report_data["row_pos"],
                2,
                float(balance.get("debit", 0.0)),
                report_data["formats"]["format_amount"],
            )
            report_data["sheet"].write_number(
                report_data["row_pos"],
                3,
                float(balance.get("credit", 0.0)),
                report_data["formats"]["format_amount"],
            )
            report_data["row_pos"] += 1

    def _generate_report_content(self, workbook, report, data, report_data):
        self.write_array_header(report_data)
        earning_account = self._get_earning_account(report.company_id)
        rounding = report.company_id.currency_id.rounding
        if len(earning_account) != 1:
            raise ValidationError(_("Company must have a profit loss account."))
        values = self.env[
            "report.account_financial_report.trial_balance"
        ]._get_report_values(report, data)
        trial_balance = values.get("trial_balance", [])
        trial_balance = sorted(
            trial_balance, key=lambda line: (line.get("code") or ""), reverse=True
        )
        for balance in trial_balance:
            if not balance.get("code", False):
                continue
            amount = balance.get("ending_balance", 0.0)
            if float_is_zero(amount, precision_rounding=rounding):
                continue
            debit, credit = self._line_to_debit_credit(amount, report.move_type)
            self._write_opening_closing_line(
                {
                    "code": balance.get("code"),
                    "name": balance.get("name"),
                    "debit": debit,
                    "credit": credit,
                },
                report_data,
            )
