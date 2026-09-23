###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderGoodsFreePartnerGroup(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_group = self.env['res.partner'].create({
            'name': 'Test partner group',
            'is_company': False,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'partner_group_id': self.partner_group.id,
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })

    def create_sale(self, partner, product, quantity):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': product.list_price,
                    'product_uom_qty': quantity,
                }),
            ],
        })
        sale.onchange_partner_id()
        return sale

    def create_goods_free(self, partner, product, percent):
        self.env['res.partner.goods_free'].create({
            'partner_id': partner.id,
            'product_id': product.id,
            'percent': percent,
        })

    def search_goods_free(self, partner, product):
        return self.env['res.partner.goods_free'].search([
            ('product_id', '=', product.id),
            ('partner_id', '=', partner.id),
        ])

    def test_goods_free_only_partner(self):
        self.create_goods_free(self.partner, self.product, 10)
        goods_free_partner = self.search_goods_free(self.partner, self.product)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        self.assertEqual(len(goods_free_partner), 1)
        self.assertEqual(len(goods_free_group), 0)
        self.assertEqual(goods_free_partner.percent, 10)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(sale.order_line[0].product_uom_qty, 10)
        self.assertEqual(
            sale.order_line[0].price_unit, self.product.list_price)
        self.assertEqual(sale.order_line[0].discount, 0)
        self.assertFalse(sale.order_line[0].line_goods_free_id)
        self.assertEqual(sale.order_line[1].product_uom_qty, 1)
        self.assertEqual(
            sale.order_line[1].price_unit, self.product.list_price)
        self.assertEqual(sale.order_line[1].discount, 100)
        self.assertTrue(sale.order_line[1].line_goods_free_id)

    def test_goods_free_only_partner_group(self):
        self.create_goods_free(self.partner_group, self.product, 20)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(self.partner, self.product)
        self.assertEqual(len(goods_free_group), 1)
        self.assertEqual(goods_free_group.percent, 20)
        self.assertEqual(len(goods_free_partner), 0)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(sale.order_line[0].product_uom_qty, 10)
        self.assertEqual(
            sale.order_line[0].price_unit, self.product.list_price)
        self.assertEqual(sale.order_line[0].discount, 0)
        self.assertFalse(sale.order_line[0].line_goods_free_id)
        self.assertEqual(sale.order_line[1].product_uom_qty, 2)
        self.assertEqual(
            sale.order_line[1].price_unit, self.product.list_price)
        self.assertEqual(sale.order_line[1].discount, 100)
        self.assertTrue(sale.order_line[1].line_goods_free_id)

    def test_goods_free_sale_partner_and_partner_group_01(self):
        self.create_goods_free(self.partner_group, self.product, 30)
        self.create_goods_free(self.partner, self.product, 40)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(self.partner, self.product)
        self.assertEqual(len(goods_free_partner), 1)
        self.assertEqual(goods_free_partner.percent, 40)
        self.assertEqual(len(goods_free_group), 1)
        self.assertEqual(goods_free_group.percent, 30)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(sale.order_line[0].product_uom_qty, 10)
        self.assertEqual(sale.order_line[1].product_uom_qty, 4)
        self.assertEqual(sale.order_line[1].discount, 100)
        self.assertTrue(sale.order_line[1].line_goods_free_id)

    def test_goods_free_sale_partner_and_partner_group_02(self):
        product = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product',
            'standard_price': 10,
            'list_price': 30,
        })
        self.create_goods_free(self.partner_group, product, 30)
        self.create_goods_free(self.partner, self.product, 50)
        goods_free_group = self.search_goods_free(self.partner_group, product)
        goods_free_partner = self.search_goods_free(self.partner, self.product)
        self.assertEqual(len(goods_free_partner), 1)
        self.assertEqual(goods_free_partner.percent, 50)
        self.assertEqual(len(goods_free_group), 1)
        self.assertEqual(goods_free_group.percent, 30)
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': self.product.list_price,
                    'product_uom_qty': 10,
                }),
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': product.list_price,
                    'product_uom_qty': 10,
                }),
            ],
        })
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 3)
        self.assertEqual(sale.order_line[0].product_uom_qty, 10)
        self.assertFalse(sale.order_line[0].line_goods_free_id)
        self.assertEqual(sale.order_line[0].discount, 0)
        self.assertEqual(sale.order_line[1].product_uom_qty, 5)
        self.assertTrue(sale.order_line[1].line_goods_free_id)
        self.assertEqual(sale.order_line[1].discount, 100)
        self.assertEqual(sale.order_line[2].product_uom_qty, 10)
        self.assertFalse(sale.order_line[2].line_goods_free_id)
        self.assertEqual(sale.order_line[2].discount, 0)

    def test_sale_without_goods_free(self):
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(self.partner, self.product)
        self.assertEqual(len(goods_free_group), 0)
        self.assertEqual(len(goods_free_partner), 0)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 1)
        self.assertEqual(sale.order_line[0].product_uom_qty, 10)
        self.assertEqual(sale.order_line[0].discount, 0)
        self.assertFalse(sale.order_line[0].line_goods_free_id)

    def test_sale_goods_free_amount_pending(self):
        self.create_goods_free(self.partner_group, self.product, 10)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(
            self.partner, self.product)
        self.assertEqual(len(goods_free_group), 1)
        self.assertEqual(len(goods_free_partner), 0)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(goods_free_group.percent, 10)
        goods_free_group.percent = 20
        self.assertEqual(goods_free_group.percent, 20)
        sale._compute_goods_free_amount_total()
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        self.assertEqual(
            sale.goods_free_amount_pending, self.product.list_price)

    def test_recompute_goods_free_01(self):
        self.create_goods_free(self.partner_group, self.product, 10)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(
            self.partner, self.product)
        self.assertEqual(len(goods_free_group), 1)
        self.assertEqual(len(goods_free_partner), 0)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        amount_total_01 = sale.goods_free_amount_total
        amount_pending_01 = sale.goods_free_amount_pending
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(goods_free_group.percent, 10)
        goods_free_group.percent = 20
        self.assertEqual(goods_free_group.percent, 20)
        sale._compute_goods_free_amount_total()
        self.assertEqual(sale.goods_free_amount_total, amount_total_01)
        self.assertEqual(
            sale.goods_free_amount_pending,
            amount_pending_01 + self.product.list_price)
        sale.action_recompute_goods_free()
        self.assertEqual(sale.goods_free_amount_total, amount_total_01 * 2)
        self.assertEqual(
            sale.goods_free_amount_total, self.product.list_price * 2)
        self.assertEqual(sale.goods_free_amount_pending, 0)

    def test_recompute_goods_free_02(self):
        self.create_goods_free(self.partner, self.product, 10)
        goods_free_group = self.search_goods_free(
            self.partner_group, self.product)
        goods_free_partner = self.search_goods_free(
            self.partner, self.product)
        self.assertEqual(len(goods_free_group), 0)
        self.assertEqual(len(goods_free_partner), 1)
        sale = self.create_sale(self.partner, self.product, 10)
        amount_total = sum(
            [line.price_unit * line.product_uom_qty for line in
                sale.order_line.filtered(lambda ln: ln.line_goods_free_id)])
        self.assertEqual(sale.goods_free_amount_total, amount_total)
        amount_total_01 = sale.goods_free_amount_total
        amount_pending_01 = sale.goods_free_amount_pending
        self.assertEqual(sale.goods_free_amount_pending, 0)
        self.assertEqual(len(sale.order_line), 2)
        self.assertEqual(goods_free_partner.percent, 10)
        goods_free_partner.percent = 20
        self.assertEqual(goods_free_partner.percent, 20)
        sale._compute_goods_free_amount_total()
        self.assertEqual(sale.goods_free_amount_total, amount_total_01)
        self.assertEqual(
            sale.goods_free_amount_pending,
            amount_pending_01 + self.product.list_price)
        sale.action_recompute_goods_free()
        self.assertEqual(sale.goods_free_amount_total, amount_total_01 * 2)
        self.assertEqual(
            sale.goods_free_amount_total, self.product.list_price * 2)
        self.assertEqual(sale.goods_free_amount_pending, 0)
