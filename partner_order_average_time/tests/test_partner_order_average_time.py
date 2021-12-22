###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPartnerOrderAverageTime(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.journal = self.env['account.journal'].search([
            ('company_id', '=', self.env.user.company_id.id),
            ('type', '=', 'sale'),
        ], limit=1)
        self.account = self.env.user.company_id.get_chart_of_accounts_or_fail()
        self.invoice = self.env['account.invoice'].create({
            'journal_id': self.journal.id,
            'partner_id': self.partner.id,
            'origin': 'Test origin',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'account_id': self.account.id,
                'price_unit': 100,
                'quantity': 1,
            })],
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        self.sale.action_confirm()
        self.sale.write({
            'confirmation_date': '2020-01-1',
        })
        self.sale2 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        self.sale2.action_confirm()
        self.sale2.write({
            'confirmation_date': '2020-01-10',
        })

    def test_average_time_last_order_date(self):
        self.assertEquals(
            self.partner.last_order_date, self.sale2.confirmation_date)
        self.assertEquals(self.partner.average_time, 4.5)

    def test_average_time_last_order_date_adding_order(self):
        sale3 = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale3.action_confirm()
        sale3.write({
            'confirmation_date': '2020-02-12',
        })
        self.assertEquals(
            self.partner.last_order_date, sale3.confirmation_date)
        self.assertEquals(self.partner.average_time, 14)
