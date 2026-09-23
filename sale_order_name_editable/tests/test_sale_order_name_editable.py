###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import Form, TransactionCase


class TestSaleOrderNameEditable(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'company_id': False,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 20,
        })

    def test_editable_only_draft(self):
        form = Form(self.env['sale.order'].with_context(
            tracking_disable=True))
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.name = self.product.name
            line.product_id = self.product
            line.product_uom_qty = 1.0
        sale = form.save()
        self.assertEqual(sale.state, 'draft')
        self.assertIn('S0', sale.name)
        sale.name = 'sale_test_001'
        self.assertEqual(sale.name, 'sale_test_001')
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')
        with self.assertRaises(AssertionError) as error:
            with Form(sale) as form:
                form.name = 'sale_test_001_modified'
                form.save()
        self.assertIn('can\'t write on readonly field', str(error.exception))

    def test_editable_name_unique(self):
        form = Form(self.env['sale.order'].with_context(
            tracking_disable=True))
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.name = self.product.name
            line.product_id = self.product
            line.product_uom_qty = 1.0
        sale_01 = form.save()
        self.assertEqual(sale_01.state, 'draft')
        self.assertIn('S0', sale_01.name)
        sale_01.name = 'sale_test_001'
        self.assertEqual(sale_01.name, 'sale_test_001')
        form = Form(self.env['sale.order'].with_context(
            tracking_disable=True))
        form.partner_id = self.partner
        with form.order_line.new() as line:
            line.name = self.product.name
            line.product_id = self.product
            line.product_uom_qty = 1.0
        sale_02 = form.save()
        self.assertEqual(sale_02.state, 'draft')
        self.assertIn('S0', sale_02.name)
        with self.assertRaises(ValidationError) as result:
            sale_02.name = 'sale_test_001'
        msg = (
            'There is already another sales order with the same name, it must '
            'be unique.')
        self.assertIn(msg, result.exception.args[0])
