###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestPurchaseSupplierinfoNocreate(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.ProductCategory = self.env['product.category']
        self.PurchaseOrder = self.env['purchase.order']
        self.ProductProduct = self.env['product.product']
        self.category_no_create = self.ProductCategory.create({
            'name': 'No Supplierinfo Creation',
            'disable_supplierinfo_creation': True,
        })
        self.category_create = self.ProductCategory.create({
            'name': 'Supplierinfo Creation',
            'disable_supplierinfo_creation': False,
        })
        self.product_no_create = self.ProductProduct.create({
            'name': 'Product No Create',
            'categ_id': self.category_no_create.id,
        })
        self.product_create = self.ProductProduct.create({
            'name': 'Product Create',
            'categ_id': self.category_create.id,
        })

    def test_supplierinfo_creation(self):
        po = self.PurchaseOrder.create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_no_create.id,
                    'product_qty': 5,
                    'price_unit': 10,
                }),
                (0, 0, {
                    'product_id': self.product_create.id,
                    'product_qty': 3,
                    'price_unit': 15,
                }),
            ],
        })
        po.button_confirm()
        supplierinfos = self.env['product.supplierinfo'].search([
            ('partner_id', '=', po.partner_id.id),
            ('product_tmpl_id', 'in', [
                self.product_no_create.product_tmpl_id.id,
                self.product_create.product_tmpl_id.id,
            ]),
        ])
        self.assertEqual(len(supplierinfos), 1)
        self.assertEqual(
            supplierinfos.product_tmpl_id,
            self.product_create.product_tmpl_id,
        )

    def test_no_delete_actual_supplierinfo(self):
        self.assertFalse(self.product_no_create.seller_ids)
        self.env['product.supplierinfo'].create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'product_tmpl_id': self.product_no_create.product_tmpl_id.id,
            'min_qty': 1,
            'price': 20,
        })
        self.assertEqual(len(self.product_no_create.seller_ids), 1)
        po = self.PurchaseOrder.create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_no_create.id,
                    'product_qty': 5,
                    'price_unit': 10,
                }),
            ],
        })
        po.button_confirm()
        supplierinfos = self.env['product.supplierinfo'].search([
            ('partner_id', '=', po.partner_id.id),
            ('product_tmpl_id', 'in', [
                self.product_no_create.product_tmpl_id.id,
            ]),
        ])
        self.assertEqual(len(supplierinfos), 1)
        self.assertEqual(
            supplierinfos.product_tmpl_id,
            self.product_no_create.product_tmpl_id,
        )
