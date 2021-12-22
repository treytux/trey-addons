###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductPricelistItemByConditions(TransactionCase):
    def setUp(self):
        super().setUp()
        self.categ_a = self.env['product.category'].create({
            'name': 'CAT-A',
        })
        self.categ_b = self.env['product.category'].create({
            'name': 'CAT-B',
        })
        self.categ_c = self.env['product.category'].create({
            'name': 'CAT-C',
        })
        self.product_a5 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test A = 5',
            'categ_id': self.categ_a.id,
            'standard_price': 5,
            'list_price': 8,
        })
        self.product_a10 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test A = 10',
            'categ_id': self.categ_a.id,
            'standard_price': 10,
            'list_price': 12,
        })
        self.product_b5 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Test B = 5',
            'categ_id': self.categ_b.id,
            'standard_price': 5,
            'list_price': 10,
        })
        self.pricelist_a = self.env['product.pricelist'].create({
            'name': 'Pricelist A (based on standard price)',
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.categ_a.id,
                'compute_price': 'condition',
                'base': 'standard_price',
                'condition_ids': [
                    (0, 0, {
                        'price_to': 5,
                        'percent_increase': 150,
                    }),
                    (0, 0, {
                        'price_to': 10,
                        'percent_increase': 200,
                    }),
                ],
            })],
        })
        conditions = self.pricelist_a.item_ids.condition_ids
        self.assertEquals(len(conditions), 2)
        condition_price_to_5 = conditions.filtered(lambda ln: ln.price_to == 5)
        self.assertEquals(condition_price_to_5.price_from, 0)
        condition_price_to_10 = conditions.filtered(
            lambda ln: ln.price_to == 10)
        self.assertEquals(condition_price_to_10.price_from, 5.01)
        self.pricelist_b = self.env['product.pricelist'].create({
            'name': 'Pricelist B (based on list price, decreases price)',
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.categ_a.id,
                'compute_price': 'condition',
                'base': 'list_price',
                'condition_ids': [
                    (0, 0, {
                        'price_to': 5,
                        'percent_increase': 50,
                    }),
                    (0, 0, {
                        'price_to': 10,
                        'percent_increase': 25,
                    }),
                ],
            })],
        })
        conditions = self.pricelist_b.item_ids.condition_ids
        self.assertEquals(len(conditions), 2)
        condition_price_to_5 = conditions.filtered(lambda ln: ln.price_to == 5)
        self.assertEquals(condition_price_to_5.price_from, 0)
        condition_price_to_10 = conditions.filtered(
            lambda ln: ln.price_to == 10)
        self.assertEquals(condition_price_to_10.price_from, 5.01)
        self.pricelist_c = self.env['product.pricelist'].create({
            'name': 'Pricelist C (based on list price, increases price)',
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.categ_a.id,
                'compute_price': 'condition',
                'base': 'list_price',
                'condition_ids': [
                    (0, 0, {
                        'price_to': 5,
                        'percent_increase': 150,
                    }),
                    (0, 0, {
                        'price_to': 10,
                        'percent_increase': 200,
                    }),
                ],
            })],
        })
        conditions = self.pricelist_c.item_ids.condition_ids
        self.assertEquals(len(conditions), 2)
        condition_price_to_5 = conditions.filtered(lambda ln: ln.price_to == 5)
        self.assertEquals(condition_price_to_5.price_from, 0)
        condition_price_to_10 = conditions.filtered(
            lambda ln: ln.price_to == 10)
        self.assertEquals(condition_price_to_10.price_from, 5.01)
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
        })

    def create_sale_order(self, partner, product, qty):
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'pricelist_id': self.partner.property_product_pricelist.id,
        })
        sale.onchange_partner_id()
        vline = self.env['sale.order.line'].new({
            'order_id': sale.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        vline.product_id_change()
        self.env['sale.order.line'].create(
            vline._convert_to_write(vline._cache))
        return sale

    def test_contraint_conditions_price_from_must_be_less_than_price_to(self):
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.categ_a.id,
                'compute_price': 'condition',
                'base': 'list_price',
                'condition_ids': [
                    (0, 0, {
                        'price_to': 5,
                        'percent_increase': 150,
                    }),
                    (0, 0, {
                        'price_to': 10,
                        'percent_increase': 200,
                    }),
                ],
            })],
        })
        conditions = pricelist.item_ids.condition_ids
        self.assertEquals(len(conditions), 2)
        condition_price_to_5 = conditions.filtered(lambda ln: ln.price_to == 5)
        self.assertEquals(condition_price_to_5.price_from, 0)
        condition_price_to_10 = conditions.filtered(
            lambda ln: ln.price_to == 10)
        self.assertEquals(condition_price_to_10.price_from, 5.01)
        with self.assertRaises(ValidationError):
            condition_price_to_10.price_to = 2

    def test_contraint_conditions_overlap(self):
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '2_product_category',
                'categ_id': self.categ_a.id,
                'compute_price': 'condition',
                'base': 'list_price',
                'condition_ids': [
                    (0, 0, {
                        'price_to': 5,
                        'percent_increase': 150,
                    }),
                    (0, 0, {
                        'price_to': 10,
                        'percent_increase': 200,
                    }),
                ],
            })],
        })
        conditions = pricelist.item_ids.condition_ids
        self.assertEquals(len(conditions), 2)
        condition_price_to_5 = conditions.filtered(lambda ln: ln.price_to == 5)
        self.assertEquals(condition_price_to_5.price_from, 0)
        condition_price_to_10 = conditions.filtered(
            lambda ln: ln.price_to == 10)
        self.assertEquals(condition_price_to_10.price_from, 5.01)
        with self.assertRaises(ValidationError):
            pricelist.item_ids.condition_ids.create({
                'pricelist_item_id': pricelist.item_ids[0].id,
                'price_to': 4,
                'percent_increase': 999,
            })

    def test_contraint_percent_increase_greater_than_zero(self):
        with self.assertRaises(ValidationError):
            self.env['product.pricelist'].create({
                'name': 'Pricelist',
                'item_ids': [(0, 0, {
                    'applied_on': '2_product_category',
                    'categ_id': self.categ_a.id,
                    'compute_price': 'condition',
                    'base': 'list_price',
                    'condition_ids': [
                        (0, 0, {
                            'price_to': 5,
                            'percent_increase': -150,
                        }),
                        (0, 0, {
                            'price_to': 10,
                            'percent_increase': 200,
                        }),
                    ],
                })],
            })

    def test_pricelist_a_product_a5(self):
        self.partner.property_product_pricelist = self.pricelist_a.id
        sale = self.create_sale_order(self.partner, self.product_a5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_a)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 7.5)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_a_product_a10(self):
        self.partner.property_product_pricelist = self.pricelist_a.id
        sale = self.create_sale_order(self.partner, self.product_a10, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_a)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 20)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_a_product_b5(self):
        self.partner.property_product_pricelist = self.pricelist_a.id
        sale = self.create_sale_order(self.partner, self.product_b5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_a)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 10)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_b_product_a5(self):
        self.partner.property_product_pricelist = self.pricelist_b.id
        sale = self.create_sale_order(self.partner, self.product_a5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_b)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 2)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_b_product_a10(self):
        self.partner.property_product_pricelist = self.pricelist_b.id
        sale = self.create_sale_order(self.partner, self.product_a10, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_b)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 12)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_b_product_b5(self):
        self.partner.property_product_pricelist = self.pricelist_b.id
        sale = self.create_sale_order(self.partner, self.product_b5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_b)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 10)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_c_product_a5(self):
        self.partner.property_product_pricelist = self.pricelist_c.id
        sale = self.create_sale_order(self.partner, self.product_a5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_c)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 16)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_c_product_a10(self):
        self.partner.property_product_pricelist = self.pricelist_c.id
        sale = self.create_sale_order(self.partner, self.product_a10, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_c)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 12)
        self.assertEquals(sale.order_line.discount, 0)

    def test_pricelist_c_product_b5(self):
        self.partner.property_product_pricelist = self.pricelist_c.id
        sale = self.create_sale_order(self.partner, self.product_b5, 1)
        self.assertEquals(sale.pricelist_id, self.pricelist_c)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line.price_unit, 10)
        self.assertEquals(sale.order_line.discount, 0)
