###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleOrderLineOptionalProductAuto(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_a = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product test A',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product_b = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product test B',
            'standard_price': 10,
            'list_price': 100,
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Product test B',
            'standard_price': 10,
            'list_price': 100,
            'optional_product_method': 'auto',
            'optional_product_ids': [
                (6, 0, [
                    self.product_a.product_tmpl_id.id,
                    self.product_b.product_tmpl_id.id,
                ]),
            ],
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })

    def test_cross_selling(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(line.order_id.sale_order_option_ids), 2)
        products = line.order_id.sale_order_option_ids.mapped('product_id')
        self.assertIn(self.product_a, products)
        self.assertIn(self.product_b, products)
        self.assertEquals(len(products), 2)
        line.product_id = self.product_a.id
        line.product_id_change()
        self.assertEquals(len(line.sale_order_option_ids), 0)

    def test_cross_selling_configure(self):
        self.product.product_tmpl_id.optional_product_method = 'configure'
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 10,
            'product_uom': self.product.uom_id.id,
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(line.order_id.sale_order_option_ids), 0)

    def test_add_section(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.env.ref('product.list0').id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'name': 'Title',
            'display_type': 'line_section',
        })
        line.product_id_change()
        line = line_obj.create(line_obj._convert_to_write(line._cache))
        self.assertEquals(len(line.order_id.sale_order_option_ids), 0)
