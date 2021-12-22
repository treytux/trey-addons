###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.website_sale_payment_direct_order.controllers.main import \
    WebsiteSale
from odoo.tests.common import HttpCase


class TestWebsiteSalePaymentDirectOrder(HttpCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })

    def get_payment_acquirers_direct_order(self, direct_order):
        if direct_order:
            return self.env['payment.acquirer'].search([
                ('provider', '=', 'direct_order'),
            ])
        return self.env['payment.acquirer'].search([
            ('provider', '!=', 'direct_order'),
        ])

    def test_website_sale_payment_direct_order(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 70,
                    'product_uom_qty': 1,
                }),
            ],
        })
        sale.action_confirm()
        self.assertEquals(self.partner.risk_sale_order, sale.amount_total)
        self.assertFalse(self.partner.risk_exception)
        controller = WebsiteSale()
        for acquirer in self.get_payment_acquirers_direct_order(False):
            self.assertTrue(
                controller.add_payment_acquirer(acquirer, sale))
        acquirers = self.get_payment_acquirers_direct_order(True)
        self.assertEquals(len(acquirers), 1)
        acquirer = acquirers[0]
        self.assertTrue(
            controller.add_payment_acquirer(acquirer, sale))
        self.partner.risk_sale_order_limit = 60
        self.assertEquals(self.partner.risk_sale_order_limit, 60)
        self.assertTrue(self.partner.risk_exception)
        sale_2 = sale.copy()
        wiz_dic = sale_2.action_confirm()
        wiz = self.env[wiz_dic['res_model']].browse(wiz_dic['res_id'])
        self.assertEqual(wiz.exception_msg, 'Financial risk exceeded.\n')
        self.assertFalse(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.risk_sale_order_limit = 140
        self.assertEquals(self.partner.risk_sale_order_limit, 140)
        wiz_dic = sale_2.action_confirm()
        wiz = self.env[wiz_dic['res_model']].browse(wiz_dic['res_id'])
        self.assertEqual(wiz.exception_msg,
                         'This sale order exceeds the sales orders risk.\n')
        self.assertTrue(
            self.partner.risk_sale_order + sale_2.amount_total > (
                self.partner.risk_sale_order_limit))
        self.assertFalse(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.risk_sale_order_limit = sale.amount_total * 2
        self.assertEquals(
            self.partner.risk_sale_order_limit, sale.amount_total * 2)
        self.assertFalse(
            self.partner.risk_sale_order + sale_2.amount_total > (
                self.partner.risk_sale_order_limit))
        self.assertTrue(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.risk_sale_order_limit = 180
        self.assertEquals(self.partner.risk_sale_order_limit, 180)
        self.assertFalse(
            self.partner.risk_sale_order + sale_2.amount_total > (
                self.partner.risk_sale_order_limit))
        self.assertTrue(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.risk_sale_order_limit = 0
        self.partner.risk_sale_order_include = True
        self.assertEquals(self.partner.risk_sale_order_limit, 0)
        self.assertTrue(self.partner.risk_sale_order_include)
        self.partner.credit_limit = 150
        self.assertEquals(self.partner.credit_limit, 150)
        wiz_dic = sale_2.action_confirm()
        wiz = self.env[wiz_dic['res_model']].browse(wiz_dic['res_id'])
        self.assertEqual(wiz.exception_msg,
                         'This sale order exceeds the financial risk.\n')
        self.assertTrue(
            self.partner.risk_total + sale_2.amount_total > (
                self.partner.credit_limit))
        self.assertFalse(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.credit_limit = sale.amount_total * 2
        self.assertEquals(self.partner.credit_limit, sale.amount_total * 2)
        self.assertFalse(
            self.partner.risk_total + sale_2.amount_total > (
                self.partner.credit_limit))
        self.assertTrue(
            controller.add_payment_acquirer(acquirer, sale_2))
        self.partner.credit_limit = 180
        self.assertEquals(self.partner.credit_limit, 180)
        self.assertFalse(
            self.partner.risk_total + sale_2.amount_total > (
                self.partner.credit_limit))
        self.assertTrue(
            controller.add_payment_acquirer(acquirer, sale_2))
