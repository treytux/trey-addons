###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os
import tempfile

import openpyxl
from odoo import exceptions
from odoo.tests import common


class TestPurchaseOrderLinesByRefXlsx(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'One',
            'list_price': 10,
            'default_code': 'R1',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'Two',
            'list_price': 20,
            'default_code': 'R2',
            'barcode': '0123456789104',
        })

    def create_wizard(self, purchase, refs):
        return self.env['purchase.order.lines_by_ref'].create({
            'purchase_id': purchase.id,
            'references': refs,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def create_xls_wizard(self, purchase, fname, filecontent):
        return self.env['purchase.order.lines_by_ref.xls'].create({
            'purchase_id': purchase.id,
            'xls_file': filecontent,
            'xls_filename': os.path.basename(fname),
        })

    def create_xlsx_sample(self, rows):
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        for row in rows:
            worksheet.append(row)
        xlsx_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        workbook.save(xlsx_file.name)
        xlsx_file.close()
        self.addCleanup(lambda: os.unlink(xlsx_file.name))
        return xlsx_file.name

    def test_import_xls_lines_ok(self):
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 8)

    def test_import_xls_lines_multiple_qty_ok(self):
        fname = self.get_sample('sample_ok_multiple_qty.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 5)
        self.assertEqual(line.price_unit, 8)

    def test_import_xlsx_lines_ok(self):
        fname = self.create_xlsx_sample([
            ['Product reference', 'Price unit', 'Product quantity'],
            ['R1', 8, 3],
        ])
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 3)
        self.assertEqual(line.price_unit, 8)

    def test_import_xlsx_lines_numeric_reference_ok(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'Barcode product',
            'list_price': 10,
            'barcode': '8437018201273',
        })
        fname = self.create_xlsx_sample([
            ['Product reference', 'Price unit', 'Product quantity'],
            [8437018201273, 8, 1],
        ])
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        self.assertEqual(purchase.order_line.product_id, product)

    def test_import_xls_lines_ok_supplierinfo_01(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': 'R2323',
            'price': 25,
        })
        fname = self.get_sample('sample_ok_supplierinfo_1.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 25)

    def test_import_xls_lines_ok_supplierinfo_02(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': 'R2323',
            'price': 25,
        })
        fname = self.get_sample('sample_ok_supplierinfo_2.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 10)

    def test_import_xls_lines_ok_supplierinfo_03(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': 'R2323',
            'price': 13,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': 'R2323',
            'price': 36,
        })
        fname = self.get_sample('sample_ok_supplierinfo_1.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 13)

    def test_import_xls_lines_error_ref_not_exists(self):
        fname = self.get_sample('sample_ref_not_exists.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 0)

    def test_import_xls_lines_error_purchase_ok_false(self):
        self.product_1.purchase_ok = False
        self.assertFalse(self.product_1.purchase_ok)
        fname = self.get_sample('sample_purchase_ok_false.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xls()
        self.assertEqual(len(purchase.order_line), 0)

    def test_import_xls_lines_error_columns_number(self):
        fname = self.get_sample('sample_error_columns_number.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(
            result.exception.args[0], 'The file must have 3 columns')
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_import_lines_from_xls()
        self.assertEqual(
            result.exception.args[0], 'The file must have 3 columns')

    def test_import_xls_lines_ok_error_columns_order(self):
        fname = self.get_sample('sample_error_columns_order.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_xls_wizard(purchase, fname, file)
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_simulate_import_lines_from_xls()
        self.assertEqual(
            result.exception.args[0], 'The columns are not in order')
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_import_lines_from_xls()
        self.assertEqual(
            result.exception.args[0], 'The columns are not in order')

    def test_purchase_order_lines_supplier(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 25,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 25)

    def test_purchase_order_lines_same_supplier_code_error(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 45,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 65,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 45)

    def test_purchase_order_lines_supplier_product_template(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'partner_id': self.partner.id,
            'product_code': '2323',
            'price': 14,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEqual(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEqual(line.product_id, self.product_1)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 14)

    def test_purchase_order_lines_supplier_product_empty_product(self):
        self.env['product.supplierinfo'].create({
            'partner_id': self.partner.id,
            'product_code': '2323',
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        wizard.action_create()
        self.assertEqual(len(purchase.order_line), 0)
        self.assertIn('not exists', wizard.line_ids[0].name)

    def test_purchase_order_lines_permission_access(self):
        user = self.env.ref('base.user_demo')
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref'].with_user(
            user=user
        ).create({
            'purchase_id': purchase.id,
            'references': '2323',
        })
        wizard.action_simulate()
