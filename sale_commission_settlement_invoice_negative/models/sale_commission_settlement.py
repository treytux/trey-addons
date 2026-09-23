###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class SaleCommissionSettlement(models.Model):
    _inherit = 'sale.commission.settlement'

    def _prepare_invoice_header(self, settlement, journal, date=False):
        res = super()._prepare_invoice_header(
            settlement=settlement, journal=journal, date=date)
        if settlement.total >= 0:
            return res
        invoice = self.env['account.invoice'].new({
            'partner_id': settlement.agent.id,
            'type': 'in_refund',
            'date_invoice': date,
            'journal_id': journal.id,
            'company_id': settlement.company_id.id,
            'state': 'draft',
        })
        invoice._onchange_partner_id()
        invoice._onchange_journal_id()
        return invoice._convert_to_write(invoice._cache)

    @api.multi
    def make_invoices(self, journal, product, date=False):
        self = self.with_context(no_check_negative=True)
        return super(SaleCommissionSettlement, self).make_invoices(
            journal=journal, product=product, date=date)
