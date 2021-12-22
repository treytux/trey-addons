###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields
from odoo.tests import common


class TestSaleValidityAutoCancel(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Product service test',
            'standard_price': 10,
            'list_price': 100,
        })

    def test_validity_auto_cancel(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.use_quotation_validity_days', True)
        self.assertEquals(
            self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_quotation_validity_days'), 'True')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        sale.date_order = datetime.now() - relativedelta(days=2)
        self.assertEquals(
            sale.date_order.date(),
            fields.Date.today() - relativedelta(days=2))
        self.assertEquals(
            sale.validity_date,
            fields.Date.today() + relativedelta(months=1))
        self.assertEquals(sale.state, 'draft')
        sale.force_quotation_send()
        self.assertEquals(sale.state, 'sent')
        sale.validity_date = fields.Date().today() - relativedelta(days=1)
        self.assertEquals(
            sale.validity_date,
            fields.Date.today() - relativedelta(days=1))
        self.assertTrue(sale.validity_date < fields.Date.today())
        self.env['sale.order'].validity_auto_cancel()
        self.assertEquals(sale.state, 'cancel')

    def test_no_cancel_sale_order_not_validity_date_yet(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.use_quotation_validity_days', True)
        self.assertEquals(
            self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_quotation_validity_days'), 'True')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertEquals(sale.state, 'draft')
        self.assertTrue(
            sale.validity_date, fields.Date.today() + relativedelta(months=1))
        sale.force_quotation_send()
        self.assertEquals(sale.state, 'sent')
        self.assertFalse(sale.validity_date < fields.Date.today())
        self.env['sale.order'].validity_auto_cancel()
        self.assertEquals(sale.state, 'sent')

    def test_no_cancel_validity_date_today(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.use_quotation_validity_days', True)
        self.assertEquals(self.env['ir.config_parameter'].sudo().get_param(
            'sale.use_quotation_validity_days'), 'True')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertEquals(sale.state, 'draft')
        sale.validity_date = fields.Date.today()
        self.assertEquals(sale.validity_date, fields.Date.today())
        self.assertEquals(sale.date_order.date(), fields.Date.today())
        sale.force_quotation_send()
        self.assertEquals(sale.state, 'sent')
        self.assertFalse(sale.validity_date < fields.Date.today())
        self.env['sale.order'].validity_auto_cancel()
        self.assertEquals(sale.state, 'sent')

    def test_validity_date_expired_and_not_state_sent(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'sale.use_quotation_validity_days', True)
        self.assertEquals(
            self.env['ir.config_parameter'].sudo().get_param(
                'sale.use_quotation_validity_days'), 'True')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1,
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2,
                }),
            ],
        })
        self.assertEquals(sale.state, 'draft')
        sale.date_order = datetime.now() - relativedelta(days=2)
        self.assertEquals(
            sale.date_order.date(),
            fields.Date.today() - relativedelta(days=2))
        self.assertEquals(
            sale.validity_date, fields.Date.today() + relativedelta(months=1))
        sale.force_quotation_send()
        self.assertEquals(sale.state, 'sent')
        sale.action_confirm()
        self.assertEquals(sale.state, 'sale')
        sale.validity_date = fields.Date.today() - relativedelta(days=1)
        self.assertTrue(sale.validity_date < fields.Date.today())
        self.env['sale.order'].validity_auto_cancel()
        self.assertEquals(sale.state, 'sale')
