###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import Form, common


class TestProductCustomerinfoFixLinePrice(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.customer = self.env['res.partner'].create({
            'name': 'Test customer',
            'is_company': True,
        })
        self.product = self.env.ref('product.product_product_4')
        self.product_variant_1 = self.env.ref('product.product_product_4b')
        self.product_variant_2 = self.env.ref('product.product_product_4c')
        self.customerinfo = self.create_partnerinfo(
            'customer', self.customer, self.product, 123)
        self.pricelist = self.create_pricelist('Test Pricelist')
        self.customerinfo_variant_1 = self.create_partnerinfo(
            'customer', self.customer, self.product_variant_1, 234)
        self.env.user.groups_id |= self.env.ref(
            'product.group_product_pricelist')

    def create_partnerinfo(
            self, supplierinfo_type, partner, product,
            price, empty_variant=False):
        vals = {
            'partner_id': partner.id,
            'product_id': product.id,
            'product_name': 'product4',
            'product_code': '00001',
            'price': price,
            'min_qty': 1.0,
        }
        if empty_variant:
            vals.pop('product_id', None)
            vals['product_tmpl_id'] = product.product_tmpl_id.id
        return self.env['product.' + supplierinfo_type + 'info'].create(vals)

    def create_pricelist(self, name):
        return self.env['product.pricelist'].create({
            'name': name,
            'currency_id': self.env.ref('base.EUR').id
        })

    def create_pricelist_item(self, name, pricelist, product, applied):
        return self.env['product.pricelist.item'].create({
            'name': name,
            'pricelist_id': pricelist.id,
            'applied_on': applied,
            'product_id': product.id,
            'compute_price': 'formula',
            'base': 'partner',
        })

    def test_product_customerinfo_set_price_sale_line_01(self):
        applied_on = '3_global'
        self.create_pricelist_item(
            'Test Pricelist Item', self.pricelist, self.product, applied_on)
        order_form = Form(self.env['sale.order'])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line = order.order_line
        self.assertIn('00001', line.name)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.price_unit, self.customerinfo.price)
        self.assertEqual(line.price_unit, 123)

    def test_product_customerinfo_set_price_sale_line_02(self):
        applied_on = '0_product_variant'
        self.create_pricelist_item(
            'Test Pricelist Item', self.pricelist, self.product, applied_on)
        order_form = Form(self.env['sale.order'])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        order = order_form.save()
        line = order.order_line
        self.assertIn('00001', line.name)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.price_unit, self.customerinfo.price)
        self.assertEqual(line.price_unit, 123)

    def test_product_customerinfo_set_price_sale_line_03(self):
        applied_on = '3_global'
        self.create_pricelist_item(
            'Test Pricelist Item', self.pricelist,
            self.product_variant_1, applied_on)
        order_form = Form(self.env['sale.order'])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_variant_1
        order = order_form.save()
        line = order.order_line
        self.assertIn('00001', line.name)
        self.assertEqual(line.product_id, self.product_variant_1)
        self.assertEqual(line.price_unit, self.customerinfo_variant_1.price)
        self.assertEqual(line.price_unit, 234)

    def test_product_customerinfo_set_price_sale_line_04(self):
        self.assertEqual(self.customerinfo_variant_1.price, 234)
        self.customerinfo_variant_1.price = 345
        self.assertEqual(self.customerinfo_variant_1.price, 345)
        applied_on = '0_product_variant'
        self.create_pricelist_item(
            'Test Pricelist Item', self.pricelist,
            self.product_variant_1, applied_on)
        order_form = Form(self.env['sale.order'])
        order_form.partner_id = self.customer
        order_form.pricelist_id = self.pricelist
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product_variant_1
        order = order_form.save()
        line = order.order_line
        self.assertIn('00001', line.name)
        self.assertEqual(line.product_id, self.product_variant_1)
        self.assertEqual(line.price_unit, self.customerinfo_variant_1.price)
        self.assertEqual(line.price_unit, 345)
