###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields
from odoo.tests.common import TransactionCase


class TestProductSupplierinfoStock(TransactionCase):

    def setUp(self):
        super().setUp()
        self.supplier = self.env['res.partner'].create({
            'name': 'Test supplier',
            'is_company': True,
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Test product template',
            'type': 'consu',
        })
        self.supplierinfo_model = self.env['product.supplierinfo']

    def _supplierinfo_vals(self, **kwargs):
        vals = {
            'partner_id': self.supplier.id,
            'product_tmpl_id': self.product_template.id,
            'min_qty': 1,
            'price': 10,
        }
        vals.update(kwargs)
        return vals

    def test_create_with_stock_sets_date_stock(self):
        supplierinfo = self.supplierinfo_model.create(
            self._supplierinfo_vals(stock=5)
        )
        self.assertEqual(supplierinfo.date_stock, fields.Date.today())

    def test_create_without_stock_does_not_set_date_stock(self):
        supplierinfo = self.supplierinfo_model.create(self._supplierinfo_vals())
        self.assertFalse(supplierinfo.date_stock)

    def test_write_with_stock_updates_date_stock(self):
        supplierinfo = self.supplierinfo_model.create(self._supplierinfo_vals())
        supplierinfo.write({
            'stock': 12,
        })
        self.assertEqual(supplierinfo.date_stock, fields.Date.today())

    def test_write_without_stock_keeps_date_stock(self):
        supplierinfo = self.supplierinfo_model.create(
            self._supplierinfo_vals(stock=2)
        )
        initial_date_stock = supplierinfo.date_stock
        supplierinfo.write({
            'price': 20,
        })
        self.assertEqual(supplierinfo.date_stock, initial_date_stock)

    def test_write_with_stock_in_batch_updates_date_stock(self):
        supplierinfo_1 = self.supplierinfo_model.create(
            self._supplierinfo_vals(product_code='SUP-001')
        )
        supplierinfo_2 = self.supplierinfo_model.create(
            self._supplierinfo_vals(product_code='SUP-002')
        )
        supplierinfos = supplierinfo_1 | supplierinfo_2
        supplierinfos.write({
            'stock': 9,
        })
        today = fields.Date.today()
        self.assertEqual(supplierinfos.mapped('date_stock'), [today, today])
