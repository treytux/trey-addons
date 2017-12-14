# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from dateutil.relativedelta import relativedelta
from openerp import api, models, fields
import logging
_log = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Contract')

    @api.multi
    def invoice_validate(self):
        if self.contract_id.exists() and self.contract_id.recurring_invoices:
            self.contract_id.date = (
                fields.Datetime.from_string(
                    self.contract_id.recurring_next_date) - relativedelta(
                    days=1))
            sum_hours = 0
            for line in self.contract_id.recurring_invoice_line_ids:
                if line.product_id.contract_hours != 0:
                    sum_hours += line.product_id.contract_hours
            self.contract_id.quantity_max = (
                self.contract_id.hours_quantity + sum_hours)
        return super(AccountInvoice, self).invoice_validate()
