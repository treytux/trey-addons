###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _prepare_analytic_lines(self):
        self.ensure_one()
        if not self.analytic_distribution_cost_center:
            return super()._prepare_analytic_lines()
        values = super()._prepare_analytic_lines()
        for account, center in self.analytic_distribution_cost_center.items():
            lines = [v for v in values if v['account_id'] == int(account)]
            lines[0]['cost_center_id'] = int(center)
        return values
