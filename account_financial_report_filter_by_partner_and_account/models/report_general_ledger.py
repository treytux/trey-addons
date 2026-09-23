###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ReportGeneralLedger(models.TransientModel):
    _inherit = 'report_general_ledger'

    def _inject_partner_values(self, only_empty_partner=False):
        def custom_execute(query, params):
            if self.filter_partner_ids and not self.filter_account_ids:
                remove = 'AND\n                ra.is_partner_account = TRUE'
                if remove in query:
                    query = query.replace(remove, '')
            return original_execute(query, params)

        original_execute = self.env.cr.execute
        self.env.cr.execute = custom_execute
        result = super()._inject_partner_values(
            only_empty_partner=only_empty_partner)
        self.env.cr.execute = original_execute
        return result
