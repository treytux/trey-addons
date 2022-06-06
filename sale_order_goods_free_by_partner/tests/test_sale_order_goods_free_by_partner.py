###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import exceptions
from odoo.tests.common import Form, TransactionCase


class TestSaleOrderGoodsFreeByPartner(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 2',
            'standard_price': 20,
            'list_price': 200,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'company_type': 'company',
        })
        self.partner_contact = self.env['res.partner'].create({
            'name': 'Partner contact test',
            'parent_id': self.partner.id,
            'company_type': 'person',
        })
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product.id,
            'percent': 10,
        })
        self.env['res.partner.goods_free'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_2.id,
            'percent': 10,
        })

    def create_sale(self, quantity, price_unit=1):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': price_unit,
                    'product_uom_qty': quantity,
                }),
            ]
        })

    def test_same_goods_free(self):
        with self.assertRaises(exceptions.ValidationError):
            self.env['res.partner.goods_free'].create({
                'partner_id': self.partner.id,
                'product_id': self.product.id,
                'percent': 50,
            })
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'price_unit': 100,
                    'product_uom_qty': 10,
                }),
            ]
        })
        self.assertEquals(len(sale.order_line), 1)

    def test_percent_one_line_simple(self):
        sale = self.create_sale(100)
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(sale.order_line[0].product_uom_qty, 100)
        self.assertEquals(sale.order_line[1].product_uom_qty, 10)
        sale.order_line[0].price_unit = 99
        self.assertEquals(sale.order_line[0].price_unit, 99)
        self.assertEquals(sale.order_line[1].price_unit, 99)
        sale.order_line[1].price_unit = 22
        self.assertEquals(sale.order_line[0].price_unit, 99)
        sale.order_line[1].refresh()
        self.assertEquals(sale.order_line[1].price_unit, 99)

    def test_percent_one_line_no_int(self):
        sale = self.create_sale(100)
        self.assertEquals(sale.order_line[0].product_uom_qty, 100)
        self.assertEquals(sale.order_line[1].product_uom_qty, 10)
        sale = self.create_sale(111)
        self.assertEquals(sale.order_line[0].product_uom_qty, 111)
        self.assertEquals(sale.order_line[1].product_uom_qty, 11)

    def test_partner(self):
        sale = self.create_sale(65, 2.1)
        sale.partner_id = self.partner_contact.id
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(sale.order_line[0].product_uom_qty, 65)
        self.assertEquals(sale.order_line[1].product_uom_qty, 6)
        new_partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'company_type': 'company',
        })
        self.partner_contact.parent_id.parent_id = new_partner.id
        sale = self.create_sale(65, 2.1)
        sale.partner_id = self.partner_contact.id
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(sale.order_line[0].product_uom_qty, 65)
        self.assertEquals(sale.order_line[1].product_uom_qty, 6)

    def test_percent_recompute_goods_free(self):
        sale = self.create_sale(65, 2.1)
        sale.partner_id = self.partner_contact.id
        sale.order_line.create({
            'order_id': sale.id,
            'product_id': self.product_2.id,
            'product_uom_qty': 101,
            'price_unit': 40,
        })
        self.assertEquals(len(sale.order_line), 4)
        self.assertEquals(sale.order_line[0].product_uom_qty, 65)
        self.assertEquals(sale.order_line[1].product_uom_qty, 6)
        self.assertEquals(sale.order_line[2].product_uom_qty, 101)
        self.assertEquals(sale.order_line[3].product_uom_qty, 10)
        self.assertEquals(sale.goods_free_amount_total, (6 * 2.1) + (10 * 40))
        total = (((65 * 2.1) + (101 * 40)) * 0.10)
        self.assertEquals(
            round(sale.goods_free_amount_pending, 2),
            round(total - sale.goods_free_amount_total, 2)
        )
        sale.action_recompute_goods_free()
        self.assertEquals(len(sale.order_line), 4)
        self.assertEquals(sale.order_line[0].product_uom_qty, 65)
        self.assertEquals(sale.order_line[1].product_uom_qty, 8)
        self.assertEquals(sale.order_line[2].product_uom_qty, 101)
        self.assertEquals(sale.order_line[3].product_uom_qty, 10)
        self.assertEquals(sale.goods_free_amount_total, (8 * 2.1) + (10 * 40))
        total = (((65 * 2.1) + (101 * 40)) * 0.10)
        self.assertEquals(
            round(sale.goods_free_amount_pending, 2),
            round(total - sale.goods_free_amount_total, 2)
        )

    def test_onchange(self):
        sale = self.create_sale(65, 2.1)
        self.assertEquals(len(sale.order_line), 2)
        sale.order_line[1].product_uom_qty = 99
        self.assertEquals(sale.order_line[1].product_uom_qty, 99)

    def test_copy(self):
        sale = self.create_sale(65, 2.1)
        self.assertEquals(len(sale.order_line), 2)
        sale_2 = sale.copy()
        self.assertEquals(len(sale_2.order_line), 2)

    def test_change_discount(self):
        sale = self.create_sale(65, 2.1)
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(sale.order_line[1].discount, 100)
        sale.order_line[1].discount = 50
        sale.order_line[1].refresh()
        self.assertEquals(sale.order_line[1].discount, 100)

    def test_percent_one_line_simple_zero(self):
        sale = self.create_sale(100)
        self.assertEquals(len(sale.order_line), 2)
        self.assertEquals(sale.order_line[0].product_uom_qty, 100)
        self.assertEquals(sale.order_line[1].product_uom_qty, 10)
        sale.order_line[0].product_uom_qty = 0
        form = Form(sale)
        self.assertEquals(len(form.order_line), 2)
