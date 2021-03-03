###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import SavepointCase


class TestProductPricelistPurchaseCumulativeDiscount(SavepointCase):

    def setUp(self):
        super().setUp()
        self.product_dto = self.env['product.product'].create({
            'name': 'Product with discount',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 1.,
        })
        self.product = self.env['product.product'].create({
            'name': 'Product 100',
            'type': 'consu',
            'lst_price': 100.0,
            'standard_price': 1.,
        })
        self.pricelist = self.env['product.pricelist.purchase'].create({
            'name': 'Supplier Pricelist',
            'type': 'purchase',
            'item_ids': [
                (0, 0, {
                    'name': 'Especific',
                    'applied_on': '0_product_variant',
                    'product_id': self.product_dto.id,
                    'compute_price': 'formula',
                    'price_discount': 50,
                    'base': 'purchase_price',
                    'cumulative_discount_ids': [
                        (0, 0, {
                            'name': 'Dto 10%',
                            'discount': 10,
                        }),
                        (0, 0, {
                            'name': 'Dto 20%',
                            'discount': 20,
                        }),
                    ],
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

    def test_puchase_pricelist(self):
        partner = self.env['res.partner'].create({
            'name': 'Partner test',
            'supplier_pricelist_id': self.pricelist.id,
        })
        supplierinfo = self.env['product.supplierinfo'].create({
            'name': partner.id,
            'price': 100,
            'discount': 11,
            'product_tmpl_id': self.product_dto.product_tmpl_id.id,
            'product_id': self.product_dto.id,
        })
        self.assertEqual(self.product_dto.lst_price, 100)
        self.assertEqual(supplierinfo.price, 100)
        self.assertEqual(supplierinfo.ref_price, 100)
        seller = self.product_dto._select_seller(
            partner_id=partner,
            quantity=1,
        )
        self.assertEqual(supplierinfo, seller)
        purchase = self.env['purchase.order'].create({
            'partner_id': partner.id,
        })
        self.assertEqual(purchase.state, 'draft')
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': self.product_dto.id,
            'quantity': 1,
        })
        line.onchange_product_id()
        line.onchange_product_id_multiple_discount()
        line._onchange_quantity()
        self.assertEqual(line.price_unit, 50)
        self.assertEqual(line.multiple_discount, '+10.0+20.0')
