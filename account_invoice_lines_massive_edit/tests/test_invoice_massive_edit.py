# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestInvoiceMassiveEdit(common.TransactionCase):

    def setUp(self):
        super(TestInvoiceMassiveEdit, self).setUp()

    def test_update_invoice(self):
        """ Update Invoice"""
        # Create product
        # product = self.env['product.product'].create({
        #     'name': ('Product for test module '
        #              'account_invoice_lines_massive_edit'),
        #     'type': 'service'})
        # Create partner
        partner = self.env['res.partner'].create({
            'name': 'Partner for test module '
                    'account_invoice_lines_massive_edit',
            'customer': True})
        # Create analytic journal
        journal = self.env['account.journal'].create({
            'name': 'Journal for test module '
                    'account_invoice_lines_massive_edit',
            'type': 'General',
            'company_id': self.env.user.company_id.id})
        # Create analytic account
        account = self.env['account.analytic.account'].create({
            'name': 'Account for test module '
                    'account_invoice_lines_massive_edit',
            'partner': partner.id,
            'type': 'contract',
            'use_timesheets': True,
            'use_tasks': True,
            'company_id': self.env.user.company_id.id})
        # Search financial account por test
        invoice = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'journal': journal.id})
        # Create analytic line for invoice
        for i in range(1, 10):
            self.env['account.invoice.line'].create({
                'invoice_id': invoice.id,
                'name': 'Line for test module '
                        'account_invoice_lines_massive_edit',
                # 'product_id': product.id,
                # 'uos_id': product.uom.id,
                'account_id': account.id,
                'journal_id': journal.id,
                'unit_price': 11.11 * i,
                'discount': 11.11 * i})
        invoice.action_lines_massive_edit()
