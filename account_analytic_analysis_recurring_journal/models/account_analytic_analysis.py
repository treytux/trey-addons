# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import api, models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    recurring_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain='[("type", "=", "sale")]')

    @api.model
    def _prepare_invoice_data(self, contract):
        invoice = super(AccountAnalyticAccount, self)._prepare_invoice_data(
            contract)
        if contract.recurring_journal_id:
            invoice['journal_id'] = contract.recurring_journal_id.id
        return invoice
