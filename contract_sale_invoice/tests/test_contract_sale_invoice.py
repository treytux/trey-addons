###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestContractLineMarkers(TransactionCase):

    def setUp(self):
        super().setUp()
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        product2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 2',
            'standard_price': 10,
            'list_price': 100,
        })
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 90,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product2.id,
                    'price_unit': 105,
                    'product_uom_qty': 2}),
            ]
        })
        self.contract_template2 = self.env['contract.template'].create({
            'name': 'Template 2',
            'contract_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': 'Services from #START# to #END#',
                    'quantity': 1,
                    'uom_id': product.uom_id.id,
                    'price_unit': 100,
                    'recurring_rule_type': 'yearly',
                    'recurring_interval': 1,
                },)
            ],
        })
        product = product.with_context(force_company=self.sale.company_id.id)
        product.write({
            'property_contract_template_id': self.contract_template2.id,
            'is_contract': True,
        })
        pricelist = self.sale.partner_id.property_product_pricelist.id
        self.contract = self.env['contract.contract'].create({
            'name': 'Test Contract 2',
            'partner_id': self.sale.partner_id.id,
            'pricelist_id': pricelist,
            'contract_type': 'sale',
            'contract_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'name': 'Services from #START# to #END#',
                    'quantity': 1,
                    'uom_id': product.uom_id.id,
                    'price_unit': 100,
                    'recurring_rule_type': 'monthly',
                    'recurring_interval': 1,
                    'date_start': '2016-02-15',
                    'recurring_next_date': '2016-02-29',
                }),
            ],
        })

    def test_same_amounts_ignore_contract_lines(self):
        self.sale.action_confirm()
        wizard = self.env['sale.advance.payment.inv'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'percentage',
            'amount': 50.0,
        })
        wizard.create_invoices()
        invoice = self.env['account.invoice'].search([
            ('origin', '=', self.sale.name),
        ])
        self.assertEquals(len(invoice), 1)
        self.assertEquals(invoice.invoice_line_ids[0].price_unit, 105)

    def test_same_amounts_ignore_contract_lines_with_downpayment(self):
        self.sale.action_confirm()
        wizard = self.env['sale.advance.payment.inv'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'percentage',
            'amount': 50.0,
        })
        wizard.create_invoices()
        invoice = self.env['account.invoice'].search([
            ('origin', '=', self.sale.name)
        ])
        self.assertEquals(len(invoice), 1)
        self.assertEquals(invoice.invoice_line_ids[0].price_unit, 105)
        wizard2 = self.env['sale.advance.payment.inv'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'percentage',
            'amount': 40.0,
        })
        wizard2.create_invoices()
        invoice2 = self.env['account.invoice'].search([
            ('origin', '=', self.sale.name),
        ], order='id desc', limit=1)
        self.assertEquals(len(invoice2), 1)
        self.assertEquals(invoice2.invoice_line_ids[0].price_unit, 84)

    def test_max_amount_reached(self):
        self.sale.action_confirm()
        wizard = self.env['sale.advance.payment.inv'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'percentage',
            'amount': 50.0,
        })
        wizard.create_invoices()
        invoice = self.env['account.invoice'].search([
            ('origin', '=', self.sale.name)
        ])
        self.assertEquals(len(invoice), 1)
        self.assertEquals(
            invoice.invoice_line_ids[0].price_unit, 105)
        wizard2 = self.env['sale.advance.payment.inv'].with_context({
            'active_ids': self.sale.ids,
            'active_id': self.sale.id,
        }).create({
            'advance_payment_method': 'percentage',
            'amount': 60.0,
        })
        with self.assertRaises(UserError):
            wizard2.create_invoices()
