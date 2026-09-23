###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import http
from odoo.addons.base.tests.common import HttpCaseWithUserDemo
from odoo.tests import tagged

from ..controllers.website_sale import WebsiteSale


@tagged('post_install', '-at_install')
class TestWebsiteSalePaymentMode(HttpCaseWithUserDemo):

    def setUp(self):
        super().setUp()
        self.partner_demo.company_id = self.env.ref('base.main_company')
        self.website = self.env.ref('website.default_website')
        self.country_id = self.env.ref('base.be').id
        self.WebsiteSaleController = WebsiteSale()
        self.default_address_values = {
            'name': 'Test Customer Address',
            'email': 'test.customer@example.com',
            'street': '123 Main Street',
            'city': 'Brussels',
            'zip': '1000',
            'country_id': self.country_id,
            'submitted': 1,
        }
        self.provider = self.env.ref('payment.payment_provider_transfer')
        self.provider.write({
            'state': 'enabled',
            'is_published': True,
        })
        self.payment_mode = self.env['account.payment.mode'].create({
            'name': 'Payment mode customer',
            'payment_method_id': self.env.ref(
                'account.account_payment_method_manual_in').id,
            'payment_type': 'inbound',
            'bank_account_link': 'variable',
        })
        self.provider.payment_mode_id = self.payment_mode.id

    def _create_so(self, partner_id=None, company_id=None):
        values = {
            'partner_id': partner_id,
            'website_id': self.website.id,
            'order_line': [(0, 0, {
                'product_id': self.env['product.product'].create({
                    'name': 'Product A',
                    'list_price': 100,
                    'website_published': True,
                    'sale_ok': True}).id,
                'name': 'Product A',
            })]
        }
        if company_id:
            values['company_id'] = company_id
        return self.env['sale.order'].create(values)

    def test_shop_payment_validate(self):
        session = self.authenticate('demo', 'demo')
        sale_order = self._create_so(partner_id=self.partner_demo.id)
        self.partner_demo.last_website_so_id = sale_order.id
        sale_order.action_confirm()
        self.assertEqual(sale_order.state, 'sale')
        transaction = self.env['payment.transaction'].create({
            'reference': 'Test Transaction',
            'provider_id': self.provider.id,
            'amount': sale_order.amount_total,
            'currency_id': sale_order.currency_id.id,
            'partner_id': self.partner_demo.id,
            'sale_order_ids': [(6, 0, [sale_order.id])],
        })
        transaction._set_pending()
        sale_order.transaction_ids = [(6, 0, [transaction.id])]
        url = f'/shop/payment/validate?sale_order_id={sale_order.id}'
        session = http.root.session_store.get(session.sid)
        session['sale_last_order_id'] = sale_order.id
        http.root.session_store.save(session)
        self.url_open(url)
        self.assertEqual(sale_order.payment_mode_id.id, self.payment_mode.id)
