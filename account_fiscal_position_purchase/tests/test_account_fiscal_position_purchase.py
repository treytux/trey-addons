###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestAccountFiscalPositionPurchase(TransactionCase):

    def setUp(self):
        super().setUp()
        self.fiscal_position_01 = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position 01',
            'country_id': self.env.ref('base.es').id,
        })
        self.fiscal_position_02 = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position 02',
            'country_id': self.env.ref('base.es').id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'customer': True,
            'is_company': True,
            'property_account_position_id': self.fiscal_position_01.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })

    def create_purchase(self):
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        purchase.onchange_partner_id()
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
        })
        line.onchange_product_id()
        line['price_unit'] = 100
        line_obj.create(line_obj._convert_to_write(line._cache))
        purchase.button_confirm()
        return purchase

    def test_purchase_fiscal_position_purchase_assigned(self):
        self.partner.property_account_position_purchase_id = (
            self.fiscal_position_02.id)
        purchase = self.create_purchase()
        self.assertEquals(purchase.fiscal_position_id, self.fiscal_position_02)
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        self.assertEquals(
            purchase.fiscal_position_id, invoice.fiscal_position_id)

    def test_purchase_fiscal_position_purchase_empty(self):
        self.partner.property_account_position_purchase_id = None
        purchase = self.create_purchase()
        self.assertEquals(purchase.fiscal_position_id, self.fiscal_position_01)
        res = purchase.with_context(create_bill=True).action_view_invoice()
        ctx = res.get('context')
        f = Form(self.env['account.invoice'].with_context(ctx),
                 view='account.invoice_supplier_form')
        invoice = f.save()
        self.assertEquals(purchase.invoice_ids, invoice)
        self.assertEquals(len(purchase.invoice_ids), 1)
        self.assertEquals(purchase.invoice_status, 'invoiced')
        self.assertEquals(
            purchase.fiscal_position_id, invoice.fiscal_position_id)

    def test_invoice_type_no_purchase(self):
        type_revenue = self.env.ref('account.data_account_type_revenue')
        type_payable = self.env.ref('account.data_account_type_payable')
        account_customer = self.env['account.account'].create({
            'name': 'Customer',
            'code': 'XX_430',
            'user_type_id': type_payable.id,
            'reconcile': True,
        })
        account_supplier = self.env['account.account'].create({
            'name': 'Supplier',
            'code': 'XX_400',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        account_sale = self.env['account.account'].create({
            'name': 'Sale',
            'code': 'XX_700',
            'user_type_id': type_revenue.id,
            'reconcile': True,
        })
        self.partner.property_account_receivable_id = account_customer.id
        self.partner.property_account_payable_id = account_supplier.id
        journal = self.env['account.journal'].create({
            'name': 'Test journal for sale',
            'type': 'sale',
            'code': 'TSALE',
            'default_debit_account_id': account_sale.id,
            'default_credit_account_id': account_sale.id,
        })
        invoice = self.env['account.invoice'].create({
            'journal_id': journal.id,
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': account_sale.id,
                'price_unit': 100,
                'quantity': 1})],
        })
        invoice.action_invoice_open()
        self.assertEquals(invoice.type, 'out_invoice')
        self.assertEquals(invoice.fiscal_position_id, self.fiscal_position_01)
        invoice_refunds = self.env['account.invoice'].search([
            ('type', '=', 'out_refund'),
        ])
        self.assertEquals(len(invoice_refunds), 0)
        self.env['account.invoice.refund'].with_context(
            active_ids=invoice.ids).create({
                'filter_refund': 'refund',
                'description': 'Refund reason',
            }).invoice_refund()
        invoice_refunds = self.env['account.invoice'].search([
            ('type', '=', 'out_refund'),
        ])
        self.assertEquals(len(invoice_refunds), 1)
        self.assertEquals(invoice_refunds.type, 'out_refund')
        self.assertEquals(
            invoice_refunds.fiscal_position_id, self.fiscal_position_01)
