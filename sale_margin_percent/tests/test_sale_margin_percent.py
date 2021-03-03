###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleMarginPercent(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 01',
            'standard_price': 80,
            'list_price': 100,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 02',
            'standard_price': 120,
            'list_price': 150,
        })

    def test_one_line(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertEqual(sale.order_line[0].margin, 20)
        self.assertEqual(sale.order_line[0].margin_percent, 20)
        self.assertEqual(sale.margin, 20)
        self.assertEqual(sale.margin_percent, 20)

    def test_several_lines_01(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 3}),
            ]
        })
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin, 40)
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin_percent, 20)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin, 90)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin_percent, 20)
        self.assertEqual(sale.margin, 40 + 90)
        self.assertEqual(sale.margin_percent, 20)

    def test_several_lines_02(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 10}),
            ]
        })
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin, 40)
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin_percent, 20)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin, 300)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin_percent, 20)
        self.assertEqual(sale.margin, 40 + 300)
        self.assertEqual(sale.margin_percent, 20)

    def test_several_lines_with_section_01(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'name': 'Note test',
                    'display_type': 'line_section'}),
            ]
        })
        self.assertEqual(sale.order_line[0].margin, 20)
        self.assertEqual(sale.order_line[0].margin_percent, 20)
        self.assertEqual(sale.margin, 20)
        self.assertEqual(sale.margin_percent, 20)

    def test_several_lines_with_section_02(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 2}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 3}),
                (0, 0, {
                    'name': 'Note test',
                    'display_type': 'line_section'}),
            ]
        })
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin, 40)
        self.assertEqual(sale.order_line[0].filtered(
            lambda l: l.product_id == self.product_01).margin_percent, 20)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin, 90)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id == self.product_02).margin_percent, 20)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id is None).margin, 0)
        self.assertEqual(sale.order_line[1].filtered(
            lambda l: l.product_id is None).margin_percent, 0)
        self.assertEqual(sale.margin, 40 + 90)
        self.assertEqual(sale.margin_percent, 20)

    def test_several_line_with_price_0(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': 0,
                    'product_uom_qty': 1}),
            ]
        })
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_01).margin, 20)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_01).margin_percent, 20)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_02).margin, -120)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_02).margin_percent, 0)
        self.assertEqual(sale.margin, -100)
        self.assertEqual(sale.margin_percent, 0)

    def test_several_line_with_qty_0(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1}),
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 0}),
            ]
        })
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_01).margin, 20)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_01).margin_percent, 20)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_02).margin, 0)
        self.assertEqual(sale.order_line.filtered(
            lambda l: l.product_id == self.product_02).margin_percent, 0)
        self.assertEqual(sale.margin, 20)
        self.assertEqual(sale.margin_percent, 20)
