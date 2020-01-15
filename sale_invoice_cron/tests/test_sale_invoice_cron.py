###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase
import datetime
from dateutil import relativedelta


class TestSaleInvoiceCron(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env.ref(
            'product.expense_hotel_product_template').product_variant_id
        sales = self.env['sale.order'].search(
            [('invoice_status', '=', 'to invoice')])
        for sale in sales:
            sale.invoice_status = 'no'
        sales = sales.search([('invoice_status', '=', 'to invoice')])
        self.assertEquals(len(sales), 0)

    def create_sale(self, name):
        sale = self.env['sale.order'].create({
            'name': name,
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'price_unit': 10,
                'product_uom_qty': 1})]
        })
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_lines:
            move.quantity_done = move.product_uom_qty
        picking.action_done()
        return sale

    def test_invoice_date(self):
        get_date = self.env['sale.order']._cron_get_invoice_date
        self.assertEquals(
            get_date(1, 0, datetime.date(2020, 2, 1)),
            datetime.date(2020, 2, 1))
        self.assertEquals(
            get_date(1, 0, datetime.date(2020, 2, 15)),
            datetime.date(2020, 2, 1))
        self.assertEquals(
            get_date(15, 0, datetime.date(2020, 2, 1)),
            datetime.date(2020, 2, 15))
        self.assertEquals(
            get_date(15, 0, datetime.date(2020, 2, 16)),
            datetime.date(2020, 2, 15))
        self.assertEquals(
            get_date(31, 0, datetime.date(2020, 2, 1)),
            datetime.date(2020, 2, 29))
        self.assertEquals(
            get_date(1, -1, datetime.date(2020, 2, 1)),
            datetime.date(2020, 1, 1))
        self.assertEquals(
            get_date(1, -1, datetime.date(2020, 2, 15)),
            datetime.date(2020, 1, 1))
        self.assertEquals(
            get_date(15, -1, datetime.date(2020, 2, 1)),
            datetime.date(2020, 1, 15))
        self.assertEquals(
            get_date(15, -1, datetime.date(2020, 2, 16)),
            datetime.date(2020, 1, 15))
        self.assertEquals(
            get_date(31, -1, datetime.date(2020, 2, 1)),
            datetime.date(2020, 1, 31))

    def test_invoice_services(self):
        sales = self.env['sale.order'].search([
            ('invoice_status', '=', 'to invoice')])
        self.assertEquals(len(sales), 0)
        invoices = sales.cron_invoice_sales()
        self.assertEquals(len(invoices), 0)
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = sales.create({
            'name': 'TEST_SALE_INVOICE_1',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        sales |= sale
        partner2 = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        sale = sales.create({
            'name': 'TEST_SALE_INVOICE_2',
            'partner_id': partner2.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sale.action_confirm()
        sales |= sale
        day = datetime.date.today().day
        self.assertEquals(
            sales._cron_get_invoice_date(day),
            datetime.date.today() + relativedelta.relativedelta(day=day))
        invoices = sales.cron_invoice_sales(day=day - 1)
        self.assertEquals(len(invoices), 0)
        invoices = sales.cron_invoice_sales(day=day)
        self.assertEquals(len(invoices), 2)
        invoices.unlink()
        invoices = sales.cron_invoice_sales(day=day + 1)
        self.assertEquals(len(invoices), 2)

    def test_cron_invoice_sales_filtered(self):
        sales = self.env['sale.order'].search([
            ('invoice_status', '=', 'to invoice')])
        self.assertEquals(len(sales), 0)
        invoices = sales.cron_invoice_sales()
        self.assertEquals(len(invoices), 0)
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = sales.create({
            'name': 'TEST_SALE_INVOICE_1',
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 2}),
            ]
        })
        sales = sale.cron_invoice_sales_filtered(False)
        self.assertEquals(len(sales), 1)
        sale.confirmation_date = False
        sales = sale.cron_invoice_sales_filtered(datetime.date.today())
        self.assertEquals(len(sales), 1)
