###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleOrderInvoiceProductCategory(TransactionCase):

    def setUp(self):
        super().setUp()
        fiscal_position_es = self.env['account.fiscal.position'].create({
            'name': 'Fiscal position es',
            'country_id': self.env.ref('base.es').id,
        })
        categ_a = self.env['product.category'].create({
            'name': 'CAT-A',
        })
        categ_b = self.env['product.category'].create({
            'name': 'CAT-B',
        })
        categ_c = self.env['product.category'].create({
            'name': 'CAT-C',
        })
        categ_a_a = self.env['product.category'].create({
            'name': 'CAT-A-A',
            'parent_id': categ_a.id,

        })
        categ_a_b = self.env['product.category'].create({
            'name': 'CAT-A-B',
            'parent_id': categ_a.id,

        })
        self.product_a = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product a',
            'default_code': 'TESTPR_A',
            'standard_price': 10,
            'list_price': 30,
            'categ_id': categ_a.id,
        })
        self.product_b = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product b',
            'default_code': 'TESTPR_B',
            'standard_price': 10,
            'list_price': 20,
            'categ_id': categ_b.id,
        })
        self.product_c = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product c',
            'default_code': 'TESTPR_C',
            'standard_price': 10,
            'list_price': 40,
            'categ_id': categ_c.id,
        })
        self.product_a_a = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product a_a',
            'default_code': 'TESTPR_A_A',
            'standard_price': 10,
            'list_price': 40,
            'categ_id': categ_a_a.id,
        })
        self.product_a_b = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product a_b',
            'default_code': 'TESTPR_A_B',
            'standard_price': 10,
            'list_price': 40,
            'categ_id': categ_a_b.id,
        })
        self.product_1_a = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 1 a',
            'default_code': 'TESTPR_1A',
            'standard_price': 10,
            'list_price': 40,
            'categ_id': categ_a.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'customer': True,
            'is_company': True,
            'property_account_position_id': fiscal_position_es.id,
            'invoice_by_product_categ_ids': [(6, 0, [categ_a.id, categ_b.id])],
        })
        self.partner_2 = self.env['res.partner'].create({
            'name': 'Test partner 2',
            'customer': True,
            'is_company': True,
            'property_account_position_id': fiscal_position_es.id,
            'invoice_by_product_categ_ids':
            [(6, 0, [categ_a.id, categ_a_a.id])],
        })
        self.partner_3 = self.env['res.partner'].create({
            'name': 'Test partner 3',
            'customer': True,
            'is_company': True,
            'property_account_position_id': fiscal_position_es.id,
        })

    def _create_invoice_from_sale(self, sales):
        data = {'advance_payment_method': 'delivered'}
        payment = self.env['sale.advance.payment.inv'].create(data)
        sale_context = {
            'active_id': sales[0].id,
            'active_ids': sales.ids,
            'active_model': 'sale.order',
            'open_invoices': True,
        }
        payment.with_context(sale_context).create_invoices()

    def test_invoice_with_one_category(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertIn(
            invoice.invoice_line_ids.product_id.categ_id,
            self.partner.invoice_by_product_categ_ids)

    def test_some_invoices_with_categories(self):
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sales = sale_1 + sale_2
        sales.action_confirm()
        self._create_invoice_from_sale(sales)
        self.assertEqual(sales[0].state, 'sale')
        self.assertEqual(len(sales[0].invoice_ids), 3)
        self.assertEqual(len(sales[1].invoice_ids), 3)
        self.assertEqual(sales[1].invoice_ids, sales[0].invoice_ids)
        invoice = sales[0].invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 2)

    def test_invoices_with_same_partner(self):
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sales = sale_1 + sale_2
        sales.action_confirm()
        self._create_invoice_from_sale(sales)
        self.assertEqual(sales[0].state, 'sale')
        self.assertEqual(len(sales[0].invoice_ids), 1)
        self.assertEqual(len(sales[1].invoice_ids), 1)
        self.assertEqual(sales[1].invoice_ids, sales[0].invoice_ids)
        invoice = sales[0].invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 2)

    def test_invoices_with_diferent_partner(self):
        sale_1 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale_2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale_3 = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sale_4 = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
            ]
        })
        sales = sale_1 + sale_2 + sale_3 + sale_4
        sales.action_confirm()
        self._create_invoice_from_sale(sales)
        for sale in sales:
            self.assertEqual(sale.state, 'sale')
        for sale in sales:
            self.assertEqual(len(sale.invoice_ids), 1)
        for sale in sales:
            self.assertEqual(sale.partner_id, sale.invoice_ids[0].partner_id)
        self.assertEqual(sales[0].invoice_ids, sales[1].invoice_ids)
        self.assertEqual(sales[2].invoice_ids, sales[3].invoice_ids)
        invoice = sales[0].invoice_ids[0]
        self.assertEqual(invoice.partner_id, sales[0].partner_id)
        self.assertEqual(invoice.partner_id, self.partner)
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        invoice_2 = sales[2].invoice_ids[0]
        self.assertEqual(invoice_2.partner_id, sales[2].partner_id)
        self.assertEqual(invoice_2.state, 'draft')
        self.assertEqual(len(invoice_2.invoice_line_ids), 2)

    def test_partner_without_categories(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_3.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_a_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 4)

    def test_partner_with_child_categories(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner_2.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_a_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_a_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 3)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertIn(
            invoice.invoice_line_ids[0].product_id.categ_id,
            self.partner_2.invoice_by_product_categ_ids)
        invoice = sale.invoice_ids[1]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertNotIn(
            invoice.invoice_line_ids.mapped('product_id').mapped('categ_id'),
            self.partner_2.invoice_by_product_categ_ids)
        invoice = sale.invoice_ids[2]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertTrue(
            invoice.invoice_line_ids.product_id.categ_id,
            self.partner_2.invoice_by_product_categ_ids)

    def test_invoice_with_and_without_categories(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_c.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 3)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertIn(
            invoice.invoice_line_ids.product_id.categ_id,
            self.partner.invoice_by_product_categ_ids)
        invoice = sale.invoice_ids[1]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertIn(
            invoice.invoice_line_ids.product_id.categ_id,
            self.partner.invoice_by_product_categ_ids)
        invoice = sale.invoice_ids[2]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertNotIn(
            invoice.invoice_line_ids.product_id.categ_id,
            self.partner.invoice_by_product_categ_ids)

    def test_invoice_lines_with_same_categories_as_partner(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_b.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 2)
        for invoice in sale.invoice_ids:
            self.assertEqual(invoice.state, 'draft')
            self.assertEqual(len(invoice.invoice_line_ids), 1)
            self.assertIn(
                invoice.invoice_line_ids.product_id.categ_id,
                self.partner.invoice_by_product_categ_ids)

    def test_invoice_same_category(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_1_a.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        self._create_invoice_from_sale(sale)
        self.assertEqual(sale.state, 'sale')
        self.assertEqual(len(sale.invoice_ids), 1)
        invoice = sale.invoice_ids[0]
        self.assertEqual(invoice.state, 'draft')
        self.assertEqual(len(invoice.invoice_line_ids), 2)
        self.assertIn(
            invoice.invoice_line_ids.mapped('product_id').mapped('categ_id'),
            self.partner.invoice_by_product_categ_ids)
