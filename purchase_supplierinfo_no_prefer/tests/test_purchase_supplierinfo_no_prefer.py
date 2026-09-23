###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestPurchaseSupplierInfoNoPrefer(TransactionCase):
    def setUp(self):
        super().setUp()
        self.supplier_1 = self.env['res.partner'].create({
            'name': 'Test supplier 1',
            'is_company': True,
            'supplier': True,
        })
        self.supplier_2 = self.env['res.partner'].create({
            'name': 'Test supplier 2',
            'is_company': True,
            'supplier': True,
        })
        self.supplier_no_prefer_1 = self.env['res.partner'].create({
            'name': 'Test supplier no prefer 1',
            'is_company': True,
            'supplier': True,
            'non_preferred_supplier': True,
        })
        self.supplier_no_prefer_2 = self.env['res.partner'].create({
            'name': 'Test supplier no prefer 2',
            'is_company': True,
            'supplier': True,
            'non_preferred_supplier': True,
        })
        self.product_a = self.env['product.template'].create({
            'type': 'consu',
            'name': 'Product template test',
        })

    def test_supplierinfo_no_prefer_onchange(self):
        self.supplier_no_prefer_1.non_preferred_supplier = False
        info_no_prefer_1 = self.env['product.supplierinfo'].create({
            'name': self.supplier_no_prefer_1.id,
            'product_tmpl_id': self.product_a.id,
        })
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_tmpl_id': self.product_a.id,
        })
        self.assertFalse(info_1.sequence < info_no_prefer_1.sequence)
        self.supplier_no_prefer_1.non_preferred_supplier = True
        self.supplier_no_prefer_1.onchange_non_preferred_supplier()
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)

    def test_supplierinfo_no_prefer(self):
        info_no_prefer_1 = self.env['product.supplierinfo'].create({
            'name': self.supplier_no_prefer_1.id,
            'product_tmpl_id': self.product_a.id,
        })
        info_1 = self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_tmpl_id': self.product_a.id,
        })
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        info_no_prefer_2 = self.env['product.supplierinfo'].create({
            'name': self.supplier_no_prefer_2.id,
            'product_tmpl_id': self.product_a.id,
        })
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        info_2 = self.env['product.supplierinfo'].create({
            'name': self.supplier_1.id,
            'product_tmpl_id': self.product_a.id,
        })
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_2.sequence)
        infos = self.env['product.supplierinfo'].search([
            ('product_tmpl_id', '=', self.product_a.id),
        ])
        info_no_prefer_1.write({'sequence': min(infos.mapped('sequence'))})
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_2.sequence)
        info_no_prefer_2.write({'sequence': min(infos.mapped('sequence'))})
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_2.sequence)
        info_1.write({'sequence': max(infos.mapped('sequence'))})
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_2.sequence)
        info_2.write({'sequence': max(infos.mapped('sequence'))})
        self.assertTrue(info_1.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_1.sequence < info_no_prefer_2.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_1.sequence)
        self.assertTrue(info_2.sequence < info_no_prefer_2.sequence)
