###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import SavepointCase


class TestAccountInvoiceCopyPlan(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountInvoiceCopyPlan, cls).setUpClass()
        cls.env.user.groups_id |= cls.env.ref('account.group_account_manager')
        type_revenue = cls.env.ref('account.data_account_type_revenue')
        type_receivable = cls.env.ref('account.data_account_type_receivable')
        tax_group_taxes = cls.env.ref('account.tax_group_taxes')
        cls.account_sale = cls.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        cls.account_customer = cls.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_receivable.id,
            'reconcile': True,
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
            'property_account_receivable_id': cls.account_customer.id,
        })
        cls.invoice_address = cls.env['res.partner'].create({
            'name': 'Partner test invoice',
            'parent_id': cls.partner.id,
            'type': 'invoice',
        })
        cls.journal_sale = cls.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': cls.account_sale.id,
            'default_credit_account_id': cls.account_sale.id,
        })
        cls.tax = cls.env['account.tax'].create({
            'name': 'Tax for sale 10%',
            'type_tax_use': 'sale',
            'tax_group_id': tax_group_taxes.id,
            'amount_type': 'percent',
            'amount': 10.0,
        })
        cls.invoice = cls.env['account.invoice'].create({
            'partner_id': cls.partner.id,
            'account_id': cls.account_customer.id,
            'type': 'out_invoice',
            'journal_id': cls.journal_sale.id,
            'payment_term_id': False,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test product',
                'account_id': cls.account_sale.id,
                'price_unit': 50,
                'quantity': 10,
                'invoice_line_tax_ids': [(6, 0, [cls.tax.id])],
            })],
        })
        cls.invoice.action_invoice_open()
        cls.env.user.lang = False

    def test_invoices(self):
        wizard = self.env['account.invoice.copy_plan'].create({
            'period': 'month',
            'quantity': 12,
        })
        wizard = wizard.with_context(active_ids=[self.invoice.id])
        invoices = wizard.create_invoices()
        self.assertEquals(len(invoices), 12)
        today = fields.Date.today()
        self.assertEquals(
            invoices[0].date_invoice, today + relativedelta(months=1))
