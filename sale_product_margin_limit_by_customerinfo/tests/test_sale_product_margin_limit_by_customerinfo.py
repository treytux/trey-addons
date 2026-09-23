###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleProductMarginLimitByCustomerInfo(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Customer test',
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'standard_price': 100.0,
            'purchase_last_price': 80.0,
            'margin_limit': 25.0,
        })
        self.env.user.sales_amount_limit = 99999999
        self.env.user.sales_discount_limit = 99.99

    def _create_sale_order(self, price_unit, discount=0.0, qty=1.0):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': qty,
                'price_unit': price_unit,
                'discount': discount,
            })],
        })

    def _create_sale_line(self, price_unit, discount=0.0, qty=1.0):
        return self._create_sale_order(
            price_unit=price_unit, discount=discount, qty=qty).order_line[0]

    def _create_customerinfo(self, margin_limit, **extra_vals):
        today = fields.Date.context_today(self.env.user)
        vals = {
            'name': self.partner.id,
            'product_tmpl_id': self.product.product_tmpl_id.id,
            'product_id': self.product.id,
            'price': 0.0,
            'margin_limit': margin_limit,
            'date_start': today,
            'date_end': today + relativedelta(days=1),
        }
        vals.update(extra_vals)
        return self.env['product.customerinfo'].create(vals)

    def test_customerinfo_margin_overrides_product_margin(self):
        self._create_customerinfo(50.0)
        line = self._create_sale_line(price_unit=150.0)
        self.assertFalse(line.is_limit_ok())
        self.assertIn(self.partner.name, line.order_id.exception_limit_reason)

    def test_customerinfo_margin_zero_is_applied(self):
        self._create_customerinfo(0.0)
        line = self._create_sale_line(price_unit=110.0)
        self.assertTrue(line.is_limit_ok())

    def test_customerinfo_out_of_date_falls_back_to_product_margin(self):
        today = fields.Date.context_today(self.env.user)
        self._create_customerinfo(
            50.0,
            date_start=today + relativedelta(days=1),
            date_end=today + relativedelta(days=2),
        )
        line = self._create_sale_line(price_unit=140.0)
        self.assertTrue(line.is_limit_ok())

    def test_customerinfo_expired_falls_back_to_product_margin(self):
        today = fields.Date.context_today(self.env.user)
        self._create_customerinfo(
            50.0,
            date_start=today - relativedelta(days=2),
            date_end=today - relativedelta(days=1),
        )
        line = self._create_sale_line(price_unit=140.0)
        self.assertTrue(line.is_limit_ok())

    def test_customerinfo_without_dates_is_applied(self):
        self._create_customerinfo(50.0, date_start=False, date_end=False)
        line = self._create_sale_line(price_unit=150.0)
        self.assertFalse(line.is_limit_ok())

    def test_customerinfo_template_margin_is_applied(self):
        self._create_customerinfo(50.0, product_id=False)
        line = self._create_sale_line(price_unit=150.0)
        self.assertFalse(line.is_limit_ok())

    def test_customerinfo_keeps_discount_limit(self):
        self.env.user.sales_discount_limit = 5.0
        self._create_customerinfo(50.0)
        line = self._create_sale_line(price_unit=230.0, discount=10.0)
        self.assertFalse(line.is_limit_ok())

    def test_customerinfo_respects_margin_ignore_flag(self):
        self.env.user.ignore_margin_price_limit = True
        self._create_customerinfo(50.0)
        line = self._create_sale_line(price_unit=180.0)
        self.assertTrue(line.is_limit_ok())

    def test_action_confirm_uses_customerinfo_margin(self):
        self._create_customerinfo(50.0)
        sale = self._create_sale_order(price_unit=170.0)
        sale.action_confirm()
        self.assertEqual(sale.state, 'sale')

    def test_action_confirm_blocks_when_customerinfo_margin_fails(self):
        self._create_customerinfo(50.0)
        sale = self._create_sale_order(price_unit=150.0)
        self.assertFalse(sale.action_confirm())
        self.assertEqual(sale.state, 'pending-approve')
