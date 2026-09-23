###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import datetime

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestAccountInvoiceAssignDateInvoice(TransactionCase):
    def setUp(self):
        super().setUp()
        self.today = datetime.date.today()
        self.partner = self.env.ref('base.res_partner_12')
        self.product = self.env.ref('product.product_product_4d')
        self.account_sale = self.env.ref('l10n_generic_coa.1_conf_a_sale')
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': self.account_sale.id,
            'default_credit_account_id': self.account_sale.id,
        })
        self.active_ids = self.env.context.get('active_ids', [])
        self.assign_date_obj = self.env['account.invoice.assign.date.invoice']
        self.invoice_assign_date = self.assign_date_obj.create({
            'date_invoice': self.today,
        })
        self.invoice_open_01 = self.env.ref('l10n_generic_coa.demo_invoice_3')
        self.invoice_open_02 = self.env.ref(
            'l10n_generic_coa.demo_invoice_followup')
        self.active_ids = self.env.context.get('active_ids', [])

    def create_invoice(self):
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'price_unit': self.product.lst_price,
                'account_id': self.account_sale.id,
                'quantity': 1})],
        })
        self.active_ids.append(invoice.id)
        self.env.context = dict(self.env.context, active_ids=self.active_ids)

    def test_invoice_assign_date(self):
        self.create_invoice()
        self.create_invoice()
        self.invoice_assign_date.assign_values_invoice()
        for invoice in self.env['account.invoice'].browse(self.active_ids):
            self.assertEqual(invoice.date_invoice, self.today)
            self.assertEqual(invoice.state, 'draft')

    def test_invoice_assign_date_raise(self):
        with self.assertRaises(UserError) as result:
            self.active_ids.append(self.invoice_open_01.id)
            self.active_ids.append(self.invoice_open_02.id)
            self.assertEqual(self.invoice_open_01.state, 'open')
            self.assertEqual(self.invoice_open_02.state, 'open')
            self.env.context = dict(
                self.env.context, active_ids=self.active_ids)
            self.invoice_assign_date.assign_values_invoice()
        self.assertIn('are not in draft state', result.exception.name)
