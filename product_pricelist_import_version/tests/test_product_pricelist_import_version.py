# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import _, fields
from dateutil.relativedelta import relativedelta
import openerp.tests.common as common
import base64
import os


class TestProductPricelistImportVersion(common.TransactionCase):

    def setUp(self):
        super(TestProductPricelistImportVersion, self).setUp()
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.pricelist_purchase = self.env['product.pricelist'].create({
            'name': 'Pricelist purchase test',
            'type': 'purchase',
        })
        self.supplier_01 = self.env['res.partner'].create({
            'name': 'Supplier 01',
            'supplier': True,
            'property_product_pricelist_purchase': self.pricelist_purchase.id,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'service',
            'default_code': 'C-16813',
            'company_id': False,
            'name': 'Product 01',
            'standard_price': 500,
            'list_price': 800,
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'service',
            'default_code': 'C-1533013',
            'company_id': False,
            'name': 'Product 02',
            'standard_price': 600,
            'list_price': 800,
        })
        self.product_03 = self.env['product.product'].create({
            'type': 'service',
            'default_code': 'C-18729',
            'company_id': False,
            'name': 'Product 02',
            'standard_price': 700,
            'list_price': 800,
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_01.product_tmpl_id.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier01 name',
            'product_code': 'SUP01_CODE',
            'pricelist_ids': [
                (0, 0, {
                    'min_quantity': 0,
                    'price': 1000,
                }),
            ],
        })
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': self.product_02.product_tmpl_id.id,
            'name': self.supplier_01.id,
            'product_name': 'Supplier02 name',
            'product_code': 'SUP02_CODE',
            'pricelist_ids': [
                (0, 0, {
                    'min_quantity': 0,
                    'price': 1000,
                }),
            ],
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def create_purchase(self, supplier):
        purchase = self.env['purchase.order'].create({
            'partner_id': supplier.id,
            'location_id': self.stock_location.id,
            'pricelist_id': supplier.property_product_pricelist_purchase.id,
        })
        return purchase

    def create_purchase_line(self, purchase, product):
        line_obj = self.env['purchase.order.line']
        line = line_obj.new({
            'order_id': purchase.id,
            'product_id': product.id,
            'name': self.product_01.name,
            'product_qty': 1,
            'date_planned': fields.Date.today(),
        })
        res = line.onchange_product_id(
            purchase.partner_id.property_product_pricelist_purchase.id,
            line.product_id.id,
            line.product_qty,
            line.product_id.uom_id.id,
            purchase.partner_id.id)
        line.price_unit = res['value']['price_unit']
        line_obj.create(line_obj._convert_to_write(line._cache))
        return line

    def test_import_pricelist_without_versions(self):
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 1)
        today = fields.Datetime.from_string(fields.Date.today())
        date_start = fields.Datetime.from_string(
            self.pricelist_purchase.version_id.date_start)
        date_end = fields.Datetime.from_string(
            self.pricelist_purchase.version_id.date_end)
        self.assertEquals(date_start, today - relativedelta(years=1))
        self.assertEquals(
            date_end, today - relativedelta(years=1) + relativedelta(days=1))
        self.assertIn(
            fields.Date.today(), self.pricelist_purchase.version_id.name)
        self.assertEquals(len(self.pricelist_purchase.version_id.items_id), 4)
        items = self.pricelist_purchase.version_id.items_id
        item_general = items.filtered(lambda it: not it.product_id)
        self.assertEquals(len(item_general), 1)
        self.assertEquals(item_general.sequence, 10)
        self.assertEquals(item_general.base, -2)
        self.assertEquals(item_general.price_discount, 0)
        item_product_01 = items.filtered(
            lambda it: it.product_id == self.product_01)
        self.assertEquals(len(item_product_01), 1)
        self.assertEquals(item_product_01.sequence, 5)
        self.assertEquals(item_product_01.base, -2)
        self.assertEquals(item_product_01.price_discount, 0.03)
        item_product_02 = items.filtered(
            lambda it: it.product_id == self.product_02)
        self.assertEquals(len(item_product_02), 1)
        self.assertEquals(item_product_02.sequence, 5)
        self.assertEquals(item_product_02.base, -2)
        self.assertEquals(item_product_02.price_discount, 0.05)
        item_product_03 = items.filtered(
            lambda it: it.product_id == self.product_03)
        self.assertEquals(len(item_product_03), 1)
        self.assertEquals(item_product_03.sequence, 5)
        self.assertEquals(item_product_03.base, -2)
        self.assertEquals(item_product_03.price_discount, 0.1)
        self.assertRaises(Exception, self.create_purchase(self.supplier_01))
        self.pricelist_purchase.version_id.date_start = fields.Date.today()
        self.pricelist_purchase.version_id.date_end = False
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 1030)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 1050)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 0)

    def test_import_pricelist_file_empty(self):
        fname = self.get_sample('sample_empty.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 0)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            _('The file does not contain data.'), wizard.line_ids.name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 0)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            _('The file does not contain data.'), wizard.line_ids.name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)

    def test_import_pricelist_last_versions_without_dates(self):
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        version = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'name': 'Version 1',
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version.id,
            'name': 'Item 1.1 (cost price)',
            'sequence': 10,
            'base': 2,
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version.id,
            'name': 'Item 1.2 (C-16813)',
            'product_id': self.product_01.id,
            'sequence': 5,
            'base': 2,
            'price_discount': -0.50,
        })
        self.assertEquals(len(self.pricelist_purchase.version_id), 1)
        self.assertFalse(self.pricelist_purchase.version_id.date_start)
        self.assertFalse(self.pricelist_purchase.version_id.date_end)
        self.assertFalse(self.pricelist_purchase.version_id.date_start)
        self.assertFalse(self.pricelist_purchase.version_id.date_end)
        self.assertEquals(self.pricelist_purchase.version_id.name, 'Version 1')
        self.assertEquals(len(self.pricelist_purchase.version_id.items_id), 2)
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 250)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 600)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 700)
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 1)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 2)
        versions = self.pricelist_purchase.version_id
        version_1 = versions.filtered(lambda v: v.name == 'Version 1')
        today = fields.Datetime.from_string(fields.Date.today())
        self.assertEquals(
            fields.Datetime.from_string(version_1.date_start),
            today - relativedelta(years=1) + relativedelta(days=2))
        self.assertFalse(version_1.date_end)
        self.assertEquals(len(version_1.items_id), 2)
        version_imported = versions.filtered(
            lambda v: 'Version imported' in v.name)
        self.assertEquals(
            fields.Datetime.from_string(version_imported.date_start),
            today - relativedelta(years=1))
        self.assertEquals(
            fields.Datetime.from_string(version_imported.date_end),
            today - relativedelta(years=1) + relativedelta(days=1))
        self.assertEquals(len(version_imported.items_id), 4)
        items = version_imported.items_id
        item_general = items.filtered(lambda it: not it.product_id)
        self.assertEquals(len(item_general), 1)
        self.assertEquals(item_general.sequence, 10)
        self.assertEquals(item_general.base, -2)
        self.assertEquals(item_general.price_discount, 0)
        item_product_01 = items.filtered(
            lambda it: it.product_id == self.product_01)
        self.assertEquals(len(item_product_01), 1)
        self.assertEquals(item_product_01.sequence, 5)
        self.assertEquals(item_product_01.base, -2)
        self.assertEquals(item_product_01.price_discount, 0.03)
        item_product_02 = items.filtered(
            lambda it: it.product_id == self.product_02)
        self.assertEquals(len(item_product_02), 1)
        self.assertEquals(item_product_02.sequence, 5)
        self.assertEquals(item_product_02.base, -2)
        self.assertEquals(item_product_02.price_discount, 0.05)
        item_product_03 = items.filtered(
            lambda it: it.product_id == self.product_03)
        self.assertEquals(len(item_product_03), 1)
        self.assertEquals(item_product_03.sequence, 5)
        self.assertEquals(item_product_03.base, -2)
        self.assertEquals(item_product_03.price_discount, 0.1)
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 250)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 600)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 700)

    def test_import_pricelist_last_versions_with_dates(self):
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        today = fields.Datetime.from_string(fields.Date.today())
        version_1 = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'name': 'Version 1',
            'date_start': today - relativedelta(years=2),
            'date_end': today - relativedelta(years=1),
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_1.id,
            'name': 'Item 1.1 (cost price)',
            'sequence': 10,
            'base': 2,
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_1.id,
            'name': 'Item 1.2 (C-16813)',
            'product_id': self.product_01.id,
            'sequence': 5,
            'base': 2,
            'price_discount': -0.50,
        })
        version_2 = self.env['product.pricelist.version'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'name': 'Version 2',
            'date_start': today - relativedelta(months=2),
            'date_end': False,
        })
        self.env['product.pricelist.item'].create({
            'price_version_id': version_2.id,
            'name': 'Item 2.1 (cost price)',
            'sequence': 10,
            'base': 2,
        })
        self.assertEquals(len(self.pricelist_purchase.version_id), 2)
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 500)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 600)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 700)
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 2)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 3)
        versions = self.pricelist_purchase.version_id
        version_1 = versions.filtered(lambda v: v.name == 'Version 1')
        today = fields.Datetime.from_string(fields.Date.today())
        self.assertEquals(
            fields.Datetime.from_string(version_1.date_start),
            today - relativedelta(years=2))
        self.assertEquals(
            fields.Datetime.from_string(version_1.date_end),
            today - relativedelta(years=1))
        self.assertEquals(len(version_1.items_id), 2)
        version_2 = versions.filtered(lambda v: v.name == 'Version 2')
        today = fields.Datetime.from_string(fields.Date.today())
        self.assertEquals(
            fields.Datetime.from_string(version_2.date_start),
            today - relativedelta(months=2))
        self.assertFalse(version_2.date_end)
        self.assertEquals(len(version_2.items_id), 1)
        version_imported = versions.filtered(
            lambda v: 'Version imported' in v.name)
        self.assertEquals(
            fields.Datetime.from_string(version_imported.date_start),
            fields.Datetime.from_string(version_1.date_start) -
            relativedelta(years=1))
        self.assertEquals(
            fields.Datetime.from_string(version_imported.date_end),
            fields.Datetime.from_string(version_1.date_start) -
            relativedelta(years=1) + relativedelta(days=1))
        self.assertEquals(len(version_imported.items_id), 4)
        items = version_imported.items_id
        item_general = items.filtered(lambda it: not it.product_id)
        self.assertEquals(len(item_general), 1)
        self.assertEquals(item_general.sequence, 10)
        self.assertEquals(item_general.base, -2)
        self.assertEquals(item_general.price_discount, 0)
        item_product_01 = items.filtered(
            lambda it: it.product_id == self.product_01)
        self.assertEquals(len(item_product_01), 1)
        self.assertEquals(item_product_01.sequence, 5)
        self.assertEquals(item_product_01.base, -2)
        self.assertEquals(item_product_01.price_discount, 0.03)
        item_product_02 = items.filtered(
            lambda it: it.product_id == self.product_02)
        self.assertEquals(len(item_product_02), 1)
        self.assertEquals(item_product_02.sequence, 5)
        self.assertEquals(item_product_02.base, -2)
        self.assertEquals(item_product_02.price_discount, 0.05)
        item_product_03 = items.filtered(
            lambda it: it.product_id == self.product_03)
        self.assertEquals(len(item_product_03), 1)
        self.assertEquals(item_product_03.sequence, 5)
        self.assertEquals(item_product_03.base, -2)
        self.assertEquals(item_product_03.price_discount, 0.1)
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 500)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 600)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 700)

    def test_import_error_file(self):
        fname = self.get_sample('sample_error.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('The first column must be called \'Default code\'!'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('The second column must be called \'Increase (%)\'!'),
            wizard.line_ids[1].name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(
            _('The first column must be called \'Default code\'!'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('The second column must be called \'Increase (%)\'!'),
            wizard.line_ids[1].name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)

    def test_product_not_found(self):
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        self.product_01.unlink()
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'file': file,
        })
        self.assertEquals(wizard.base, 'supplierinfo_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            _('No product was found with the default code \'C-16813\'.'),
            wizard.line_ids.name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 1)
        self.assertIn(
            _('No product was found with the default code \'C-16813\'.'),
            wizard.line_ids.name)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)

    def test_import_pricelist_without_versions_base_cost_price(self):
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        fname = self.get_sample('sample_ok.xls')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.product.pricelist.increase'].create({
            'pricelist_id': self.pricelist_purchase.id,
            'base': 'cost_price',
            'file': file,
        })
        self.assertEquals(wizard.base, 'cost_price')
        wizard.action_import_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 0)
        wizard.action_import_real()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        self.assertEquals(len(self.pricelist_purchase.version_id), 1)
        today = fields.Datetime.from_string(fields.Date.today())
        date_start = fields.Datetime.from_string(
            self.pricelist_purchase.version_id.date_start)
        date_end = fields.Datetime.from_string(
            self.pricelist_purchase.version_id.date_end)
        self.assertEquals(date_start, today - relativedelta(years=1))
        self.assertEquals(
            date_end, today - relativedelta(years=1) + relativedelta(days=1))
        self.assertIn(
            fields.Date.today(), self.pricelist_purchase.version_id.name)
        self.assertEquals(len(self.pricelist_purchase.version_id.items_id), 4)
        items = self.pricelist_purchase.version_id.items_id
        item_general = items.filtered(lambda it: not it.product_id)
        self.assertEquals(len(item_general), 1)
        self.assertEquals(item_general.sequence, 10)
        self.assertEquals(item_general.base, 2)
        self.assertEquals(item_general.price_discount, 0)
        item_product_01 = items.filtered(
            lambda it: it.product_id == self.product_01)
        self.assertEquals(len(item_product_01), 1)
        self.assertEquals(item_product_01.sequence, 5)
        self.assertEquals(item_product_01.base, 2)
        self.assertEquals(item_product_01.price_discount, 0.03)
        item_product_02 = items.filtered(
            lambda it: it.product_id == self.product_02)
        self.assertEquals(len(item_product_02), 1)
        self.assertEquals(item_product_02.sequence, 5)
        self.assertEquals(item_product_02.base, 2)
        self.assertEquals(item_product_02.price_discount, 0.05)
        item_product_03 = items.filtered(
            lambda it: it.product_id == self.product_03)
        self.assertEquals(len(item_product_03), 1)
        self.assertEquals(item_product_03.sequence, 5)
        self.assertEquals(item_product_03.base, 2)
        self.assertEquals(item_product_03.price_discount, 0.1)
        self.assertRaises(Exception, self.create_purchase(self.supplier_01))
        self.pricelist_purchase.version_id.date_start = fields.Date.today()
        self.pricelist_purchase.version_id.date_end = False
        purchase = self.create_purchase(self.supplier_01)
        self.assertEquals(purchase.pricelist_id, self.pricelist_purchase)
        purchase_line = self.create_purchase_line(purchase, self.product_01)
        self.assertEquals(purchase_line.price_unit, 515)
        purchase_line = self.create_purchase_line(purchase, self.product_02)
        self.assertEquals(purchase_line.price_unit, 630)
        purchase_line = self.create_purchase_line(purchase, self.product_03)
        self.assertEquals(purchase_line.price_unit, 770)
