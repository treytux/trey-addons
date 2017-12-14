# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestUnlinkInvoice(common.TransactionCase):

    def setUp(self):
        super(TestUnlinkInvoice, self).setUp()

    def test_unlink_invoice(self):
        """ Create and Unlink Invoice from account analytic line"""
        # Create product
        product = self.env['product.product'].create({
            'name': ('Product for test module '
                     'account_analytic_line_unlink_invoice_reference'),
            'list_price': 10.00,
            'type': 'service'})

        # Create partner
        partner = self.env['res.partner'].create({
            'name': 'Partner for test module '
                    'account_analytic_line_unlink_invoice_reference',
            'customer': True})

        # Create analytic journal
        journal = self.env['account.analytic.journal'].create({
            'name': 'Journal for test module '
                    'account_analytic_line_unlink_invoice_reference',
            'type': 'General',
            'company_id': self.env.user.company_id.id})

        # Create analytic account
        account = self.env['account.analytic.account'].create({
            'name': 'Account for test module '
                    'account_analytic_line_unlink_invoice_reference',
            'partner': partner.id,
            'type': 'contract',
            'use_timesheets': True,
            'use_tasks': True,
            'company_id': self.env.user.company_id.id})

        # Search financial account por test
        financial_accounts = self.env['account.account'].search([
            ('type', '=', 'sale')])

        # Create analytic line for invoice
        self.env['account.analytic.line'].create({
            'name': 'Line for test module '
                    'account_analytic_line_unlink_invoice_reference',
            'account_id': account.id,
            'journal_id': journal.id,
            'amount': 99.99,
            'product_id': product.id,
            'unit_amount': 10,
            'product_uom_id': product.uom.id,
            'general_account_id': financial_accounts[0].id})

        # Create invoice from account line
        # @todo

        # Remove invoice reference
        # @todo
