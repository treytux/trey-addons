###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import exceptions
from odoo.tests import common


class TestPurchaseOrderLinesByRefXlsx(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'supplier': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'One',
            'standard_price': 10,
            'default_code': 'R1',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'service',
            'purchase_ok': True,
            'name': 'Two',
            'standard_price': 20,
            'default_code': 'R2',
            'barcode': '0123456789104',
        })

    def create_wizard(self, purchase, refs):
        wizard_obj = self.env['purchase.order.lines_by_ref'].with_context(
            active_id=purchase.id)
        return wizard_obj.create({
            'references': refs,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def test_import_xlsx_lines_ok(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 8)

    def test_import_xlsx_lines_multiple_qty_ok(self):
        fname = self.get_sample('sample_ok_multiple_qty.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 5)
        self.assertEquals(line.price_unit, 8)

    def test_import_xlsx_lines_ok_supplierinfo_01(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': 'R2323',
            'price': 25,
        })
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 25)

    def test_import_xlsx_lines_ok_no_supplierinfo(self):
        fname = self.get_sample('sample_ok_product_list_price.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, self.product_1.standard_price)

    def test_import_xlsx_lines_ok_supplierinfo_02(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': 'R2323',
            'price': 25,
        })
        fname = self.get_sample('sample_ok_supplierinfo_2.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 10)

    def test_import_xlsx_lines_ok_supplierinfo_03(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': 'R2323',
            'price': 13,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': 'R2323',
            'price': 36,
        })
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 13)

    def test_import_xlsx_lines_ok_supplierinfo_product_code_zero_04(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': '9128812',
            'price': 35,
        })
        fname = self.get_sample('sample_ok_ends_zero.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 100)
        self.assertEquals(line.price_unit, 18)

    def test_import_xlsx_lines_error_ref_not_exists(self):
        fname = self.get_sample('sample_ref_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 0)

    def test_import_xlsx_lines_error_purchase_ok_false(self):
        self.product_1.purchase_ok = False
        self.assertFalse(self.product_1.purchase_ok)
        fname = self.get_sample('sample_purchase_ok_false.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 0)

    def test_import_xlsx_lines_error_columns_number(self):
        fname = self.get_sample('sample_error_columns_number.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_simulate_import_lines_from_xlsx()
        self.assertEqual(result.exception.name, 'The file must have 3 columns')
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_import_lines_from_xlsx()
        self.assertEqual(result.exception.name, 'The file must have 3 columns')

    def test_purchase_order_lines_supplier(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': '2323',
            'price': 25,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 25)

    def test_purchase_order_lines_same_supplier_code_error(self):
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': '2323',
            'price': 45,
        })
        self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': '2323',
            'price': 65,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 45)

    def test_purchase_order_lines_supplier_product_template(self):
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.partner.id,
            'product_code': '2323',
            'price': 14,
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 14)

    def test_purchase_order_lines_supplier_product_empty_product(self):
        self.env['product.supplierinfo'].create({
            'name': self.partner.id,
            'product_code': '2323',
        })
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(purchase, '2323')
        wizard.action_simulate()
        wizard.action_create()
        self.assertEquals(len(purchase.order_line), 0)
        self.assertIn('not exists', wizard.line_ids[0].name)

    def test_purchase_order_lines_permission_access(self):
        user = self.env.ref('base.user_demo')
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard_obj = self.env['purchase.order.lines_by_ref'].sudo(user=user)
        wizard = wizard_obj.with_context(active_id=purchase.id).create({
            'references': '2323',
        })
        wizard.action_simulate()

    def test_import_xlsx_lines_ok_price_zero_supplierinfo_01(self):
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(supplierinfo.price, 0)
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEqual(self.product_1.standard_price, 10)
        self.assertEquals(line.price_unit, 10)

    def test_import_xlsx_lines_ok_price_zero_supplierinfo_02(self):
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(supplierinfo.price, 0)
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEqual(self.product_1.standard_price, 10)
        self.assertEquals(line.price_unit, 10)

    def test_import_xlsx_lines_ok_price_zero_supplierinfo_03(self):
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'name': self.partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(supplierinfo.price, 0)
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEqual(self.product_1.standard_price, 10)
        self.assertEquals(line.price_unit, 10)

    def test_import_xlsx_lines_product_code_search_supplierinfos_01(self):
        self.product_1.barcode = 'R2323'
        self.assertEqual(self.product_1.barcode, 'R2323')
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.partner.id,
            'price': 4,
        })
        self.assertFalse(supplierinfo.product_code)
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEqual(self.product_1.standard_price, 10)
        self.assertEquals(line.price_unit, 4)

    def test_import_xlsx_lines_product_code_search_supplierinfos_02(self):
        self.product_1.barcode = 'R2323'
        self.assertEqual(self.product_1.barcode, 'R2323')
        supplierinfo = self.env['product.supplierinfo'].create({
            'product_id': self.product_1.id,
            'product_tmpl_id': self.product_1.product_tmpl_id.id,
            'name': self.partner.id,
        })
        self.assertEqual(supplierinfo.price, 0)
        self.assertFalse(supplierinfo.product_code)
        fname = self.get_sample('sample_ok_supplierinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        purchase = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['purchase.order.lines_by_ref.xlsx'].with_context(
            active_id=purchase.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(purchase.order_line), 1)
        line = purchase.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEqual(self.product_1.standard_price, 10)
        self.assertEqual(line.price_unit, 10)
