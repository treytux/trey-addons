###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import exceptions, fields
from odoo.tests import common


class TestProductSelectSeller(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.buy_route = self.env.ref('purchase_stock.route_warehouse0_buy')
        self.mto_route = self.env.ref('stock.route_warehouse0_mto')
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier test 1',
            'supplier': True,
        })
        self.supplier_02 = self.supplier_01.copy({
            'name': 'Supplier test 2',
        })
        self.customer_01 = self.env['res.partner'].create({
            'name': 'Customer test 1',
            'customer': True,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 1',
            'standard_price': 10,
            'list_price': 30,
            'route_ids': [(6, 0, [self.mto_route.id, self.buy_route.id])],
        })
        self.supplierinfo = self.env['product.supplierinfo'].create({
            'name': self.supplier_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 20,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test 2',
            'standard_price': 20,
            'list_price': 40,
            'route_ids': [(6, 0, [self.mto_route.id, self.buy_route.id])],
        })
        self.sale = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_01.id,
                    'price_unit': self.product_01.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.product_01.route_ids[0].id,
                }),
            ],
        })

    def test_product_select_seller_01(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.customer_01.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_02.id,
                    'price_unit': self.product_02.list_price,
                    'product_uom_qty': 1,
                    'route_id': self.product_02.route_ids[0].id,
                }),
            ],
        })
        with self.assertRaises(exceptions.UserError) as result:
            sale.action_confirm()
        self.assertEqual(
            result.exception.name,
            'There is no vendor associated to the product %s.'
            ' Please define a vendor for this product.' % self.product_02.name)

    def test_product_select_seller_02(self):
        supplierinfos = self.env['product.supplierinfo'].search([
            ('name', '=', self.supplier_01.id),
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 1)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        self.assertEquals(purchase_order.partner_id, self.supplier_01)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfos[0].price)

    def test_product_select_seller_03(self):
        self.env['product.supplierinfo'].create({
            'name': self.supplier_02.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 35,
        })
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 2)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        supplierinfo = supplierinfos.filtered(
            lambda s: s.name == purchase_order.partner_id)
        self.assertEquals(purchase_order.partner_id, supplierinfo.name)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo.price)

    def test_product_select_seller_04(self):
        self.env['product.supplierinfo'].create({
            'name': self.supplier_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 35,
        })
        supplierinfo_01 = self.env['product.supplierinfo'].create({
            'name': self.supplier_02.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 17,
        })
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 3)
        sellers = self.product_01.seller_ids.filtered(
            lambda s: s.name == self.supplier_01)
        self.assertEquals(len(sellers), 2)
        for seller in sellers:
            seller.sequence = 2
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(purchase_order.partner_id, self.supplier_02)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo_01.price)

    def test_product_select_seller_05(self):
        self.supplier_02.parent_id = self.supplier_01.id
        self.assertEquals(self.supplier_02.parent_id, self.supplier_01)
        self.env['product.supplierinfo'].create({
            'name': self.supplier_02.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 62,
            'sequence': 2,
        })
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 2)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        supplierinfo = supplierinfos.filtered(
            lambda s: s.name == purchase_order.partner_id)
        self.assertEquals(purchase_order.partner_id, supplierinfo.name)
        self.assertEquals(purchase_order.partner_id, self.supplier_01)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo.price)

    def test_product_select_seller_06(self):
        self.supplierinfo.sequence = 2
        self.assertEquals(self.supplierinfo.sequence, 2)
        self.supplier_02.parent_id = self.supplier_01.id
        self.assertEquals(self.supplier_02.parent_id, self.supplier_01)
        self.env['product.supplierinfo'].create({
            'name': self.supplier_02.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 62,
            'sequence': 1,
        })
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 2)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        supplierinfo = supplierinfos.filtered(
            lambda s: s.name == purchase_order.partner_id)
        self.assertEquals(purchase_order.partner_id, supplierinfo.name)
        self.assertEquals(purchase_order.partner_id, self.supplier_02)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo.price)

    def test_product_select_seller_validation_date(self):
        self.supplierinfo.write({
            'date_start': fields.Date.today() - relativedelta(days=4),
            'date_end': fields.Date.today() - relativedelta(days=2),
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': self.supplier_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 40,
            'sequence': 2,
        })
        self.assertEquals(supplierinfo.sequence, 2)
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 2)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        self.assertEquals(purchase_order.partner_id, self.supplier_01)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo.price)

    def test_product_select_seller_min_qty(self):
        self.supplierinfo.write({
            'min_qty': 2,
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': self.supplier_01.id,
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'price': 40,
            'sequence': 2,
        })
        self.assertEquals(supplierinfo.sequence, 2)
        supplierinfos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
        ])
        self.assertEquals(len(supplierinfos), 2)
        self.sale.action_confirm()
        self.assertEquals(self.sale.state, 'sale')
        purchase_order = self.env['purchase.order'].search([
            ('origin', 'ilike', self.sale.name),
        ])
        self.assertEquals(len(purchase_order), 1)
        self.assertEquals(len(purchase_order.order_line), 1)
        self.assertEquals(
            purchase_order.order_line[0].product_id, self.product_01)
        self.assertEquals(purchase_order.partner_id, self.supplier_01)
        self.assertEquals(
            purchase_order.order_line[0].price_unit, supplierinfo.price)
