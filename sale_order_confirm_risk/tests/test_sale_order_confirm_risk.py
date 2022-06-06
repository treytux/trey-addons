###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderConfirmRisk(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 20,
        })

    def test_check_no_sales_order_with_financial_risk(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.assertEqual(self.partner.risk_sale_order, 0)
        self.assertFalse(self.partner.risk_exception)
        self.partner.risk_sale_order_limit = 130.0
        self.assertFalse(self.partner.risk_exception)
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[sale.id]).create({})
        self.assertTrue(wizard.line_ids)
        self.assertFalse(wizard.financial_risk_line_ids)
        self.assertEqual(wizard.line_ids[0].wizard_id, wizard)
        self.assertEqual(wizard.line_ids[0].sale_id, sale)
        self.assertEqual(wizard.line_ids[0].partner_id, self.partner)
        self.assertEqual(wizard.line_ids[0].amount_total, sale.amount_total)
        self.assertTrue(wizard.line_ids[0].is_confirm)
        self.assertEqual(sale.state, 'draft')
        wizard.button_accept()
        self.assertEqual(sale.state, 'sale')

    def test_sales_with_financial_risk_and_without_financial_risk_01(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(self.partner.risk_sale_order, sale.amount_total)
        self.assertFalse(self.partner.risk_exception)
        self.partner.risk_sale_order_limit = 99.0
        self.assertTrue(self.partner.risk_exception)
        sale_02 = sale.copy()
        self.assertEqual(sale_02.state, 'draft')
        sale_03 = sale.copy()
        self.assertEqual(sale_03.state, 'draft')
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        sale_03.partner_id = partner.id
        self.assertEqual(sale_03.partner_id, partner)
        self.assertFalse(partner.risk_exception)
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[sale_02.id, sale_03.id]).create({})
        self.assertTrue(wizard.line_ids)
        self.assertTrue(wizard.financial_risk_line_ids)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(len(wizard.financial_risk_line_ids), 1)
        self.assertEqual(wizard.line_ids[0].partner_id, partner)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].partner_id, self.partner)
        self.assertEqual(wizard.line_ids[0].sale_id, sale_03)
        self.assertEqual(wizard.financial_risk_line_ids[0].sale_id, sale_02)
        self.assertEqual(wizard.line_ids[0].amount_total, sale_03.amount_total)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].amount_total,
            sale_02.amount_total)
        self.assertTrue(wizard.line_ids[0].is_confirm)
        self.assertFalse(wizard.financial_risk_line_ids[0].is_confirm)
        self.assertEqual(sale_02.state, 'draft')
        self.assertEqual(sale_03.state, 'draft')
        self.assertFalse(wizard.financial_risk_line_ids[0].is_confirm)
        wizard.button_accept()
        self.assertEqual(sale_02.state, 'draft')
        self.assertEqual(sale_03.state, 'sale')

    def test_sales_with_financial_risk_and_without_financial_risk_02(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(self.partner.risk_sale_order, sale.amount_total)
        self.assertFalse(self.partner.risk_exception)
        self.partner.risk_sale_order_limit = 99.0
        self.assertTrue(self.partner.risk_exception)
        sale_02 = sale.copy()
        self.assertEqual(sale_02.state, 'draft')
        sale_03 = sale.copy()
        self.assertEqual(sale_03.state, 'draft')
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        sale_03.partner_id = partner.id
        self.assertEqual(sale_03.partner_id, partner)
        self.assertFalse(partner.risk_exception)
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[sale_02.id, sale_03.id]).create({})
        self.assertTrue(wizard.line_ids)
        self.assertTrue(wizard.financial_risk_line_ids)
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(len(wizard.financial_risk_line_ids), 1)
        self.assertEqual(wizard.line_ids[0].partner_id, partner)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].partner_id, self.partner)
        self.assertEqual(wizard.line_ids[0].sale_id, sale_03)
        self.assertEqual(wizard.financial_risk_line_ids[0].sale_id, sale_02)
        self.assertEqual(wizard.line_ids[0].amount_total, sale_03.amount_total)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].amount_total,
            sale_02.amount_total)
        self.assertTrue(wizard.line_ids[0].is_confirm)
        self.assertFalse(wizard.financial_risk_line_ids[0].is_confirm)
        self.assertEqual(sale_02.state, 'draft')
        self.assertEqual(sale_03.state, 'draft')
        wizard.financial_risk_line_ids[0].is_confirm = True
        self.assertTrue(wizard.financial_risk_line_ids[0].is_confirm)
        wizard.button_accept()
        self.assertEqual(sale_02.state, 'sale')
        self.assertEqual(sale_03.state, 'sale')

    def test_check_sales_order_confirm_with_financial_risk_01(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEqual(self.partner.risk_sale_order, sale.amount_total)
        self.assertFalse(self.partner.risk_exception)
        self.partner.risk_sale_order_limit = 99.0
        self.assertTrue(self.partner.risk_exception)
        sale_02 = sale.copy()
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[sale_02.id]).create({})
        self.assertFalse(wizard.line_ids)
        self.assertTrue(wizard.financial_risk_line_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(len(wizard.financial_risk_line_ids), 1)
        self.assertEqual(wizard.financial_risk_line_ids[0].wizard_id, wizard)
        self.assertEqual(wizard.financial_risk_line_ids[0].sale_id, sale_02)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].partner_id, self.partner)
        self.assertEqual(
            wizard.financial_risk_line_ids[0].amount_total, sale.amount_total)
        self.assertFalse(wizard.financial_risk_line_ids[0].is_confirm)
        self.assertEqual(sale_02.state, 'draft')
        wizard.button_accept()
        self.assertEqual(sale_02.state, 'draft')

    def test_check_sales_order_confirm_with_financial_risk_02(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                })
            ],
        })
        sale.action_confirm()
        self.assertEqual(self.partner.risk_sale_order, sale.amount_total)
        self.assertFalse(self.partner.risk_exception)
        self.partner.risk_sale_order_limit = 99.0
        self.assertTrue(self.partner.risk_exception)
        sale_02 = sale.copy()
        wizard = self.env['sale.order.confirm'].with_context(
            active_ids=[sale_02.id]).create({})
        self.assertFalse(wizard.line_ids)
        self.assertTrue(wizard.financial_risk_line_ids)
        self.assertEqual(len(wizard.line_ids), 0)
        self.assertEqual(len(wizard.financial_risk_line_ids), 1)
        self.assertFalse(wizard.financial_risk_line_ids[0].is_confirm)
        wizard.financial_risk_line_ids[0].is_confirm = True
        self.assertEqual(sale_02.state, 'draft')
        wizard.button_accept()
        self.assertEqual(sale_02.state, 'sale')
