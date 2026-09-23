###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ContractContract(models.Model):
    _inherit = 'contract.contract'

    @api.model
    def cron_recurring_create_invoice(self, date_ref=None):
        return super(
            ContractContract,
            self.with_context(
                skip_date_start_last_date_invoiced_check=True,
            ),
        ).cron_recurring_create_invoice(date_ref)

    @api.multi
    def recurring_create_invoice(self):
        return super(
            ContractContract,
            self.with_context(
                skip_date_start_last_date_invoiced_check=True,
            ),
        ).recurring_create_invoice()
