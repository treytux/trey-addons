###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase


class TestPricelistPurchase(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_50 = cls.env['product.product'].create({
            'name': 'Product 50',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 1.,
        })
        cls.product_100 = cls.env['product.product'].create({
            'name': 'Product 100',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 1.,
        })
        cls.pricelist = cls.env['product.pricelist.purchase'].create({
            'name': 'Supplier Pricelist',
            'type': 'purchase',
            'item_ids': [
                (0, 0, {
                    'name': 'Especific',
                    'applied_on': '0_product_variant',
                    'product_id': cls.product_50.id,
                    'compute_price': 'formula',
                    'price_discount': 50,
                    'base': 'purchase_price',
                }),
                (0, 0, {
                    'name': 'All products',
                    'applied_on': '3_global',
                    'compute_price': 'formula',
                    'price_discount': 0,
                    'base': 'purchase_price',
                }),
            ]
        })

    def test_pricelist(self):
        pricelist = self.env.ref('product.list0')
        context = {'pricelist': pricelist.id, 'quantity': 1}
        product_100 = self.product_100.with_context(context)
        self.assertEqual(product_100.price, 100.0)
        product_50 = self.product_50.with_context(context)
        self.assertEqual(product_50.price, 100.0)
        self.assertEqual(self.pricelist.item_ids[0].base, 'purchase_price')

    def test_puchase_without_pricelist(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': partner.id,
            'price': 100,
            'product_tmpl_id': self.product_100.product_tmpl_id.id,
            'product_id': self.product_100.id,
        })
        seller = self.product_100._select_seller(
            partner_id=partner,
            quantity=1,
        )
        self.assertEqual(supplierinfo, seller)
        self.assertEqual(seller.price, 100)
        self.assertEqual(seller.ref_price, 100)
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        self.assertEqual(purchase.state, 'draft')
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'purchase_id': purchase.id,
            'product_id': self.product_100.id,
            'quantity': 1,
        })
        line.onchange_product_id()
        self.assertEqual(line.price_unit, 100)

    def test_puchase_pricelist_100(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier_pricelist_id': self.pricelist.id,
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': partner.id,
            'price': 100,
            'product_tmpl_id': self.product_100.product_tmpl_id.id,
            'product_id': self.product_100.id,
        })
        seller = self.product_100._select_seller(
            partner_id=partner,
            quantity=1,
        )
        self.assertEqual(supplierinfo, seller)
        self.assertEqual(seller.price, 100)
        self.assertEqual(seller.ref_price, 100)
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        self.assertEqual(purchase.state, 'draft')
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'purchase_id': purchase.id,
            'product_id': self.product_100.id,
            'quantity': 1,
        })
        line.onchange_product_id()
        self.assertEqual(line.price_unit, 100)

    def test_puchase_pricelist_50(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier_pricelist_id': self.pricelist.id,
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': partner.id,
            'price': 10,
            'product_tmpl_id': self.product_50.product_tmpl_id.id,
            'product_id': self.product_50.id,
        })
        self.assertEqual(self.product_50.lst_price, 100)
        self.assertEqual(supplierinfo.price, 10)
        self.assertEqual(supplierinfo.ref_price, 10)
        seller = self.product_50._select_seller(
            partner_id=partner,
            quantity=1,
        )
        self.assertEqual(supplierinfo, seller)
        self.assertEqual(self.product_50.lst_price, 100)
        self.assertEqual(seller.ref_price, 10)
        self.assertEqual(seller.price, 5)
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        self.assertEqual(purchase.state, 'draft')
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product_50.id,
            'quantity': 1,
        })
        line.onchange_product_id()
        line._onchange_quantity()
        self.assertEqual(line.price_unit, 5)
        self.pricelist.item_ids[0].base = 'standard_price'
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product_50.id,
            'quantity': 1,
        })
        line.onchange_product_id()
        line._onchange_quantity()
        self.assertEqual(line.price_unit, 0.5)
