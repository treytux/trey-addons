###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import _
from odoo.tests.common import TransactionCase


class TestImportTemplateSalePricelistItem(TransactionCase):
    def setUp(self):
        super().setUp()
        self.categ_1 = self.env['product.category'].create({
            'name': 'Categ 1',
        })
        self.categ_1_1 = self.env['product.category'].create({
            'name': 'Categ 1.1',
            'parent_id': self.categ_1.id,
        })
        self.categ_1_1_1 = self.env['product.category'].create({
            'name': 'Categ 1.1.1',
            'parent_id': self.categ_1_1.id,
        })
        self.product_01 = self.env['product.product'].create({
            'name': 'Test Product 01',
            'type': 'service',
            'default_code': 'PROD1TEST',
            'standard_price': 80,
            'list_price': 100,
        })

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def get_file_name(self, fname):
        return fname.split('/')[-1:][0]

    def test_import_create_applied_on_category_error(self):
        fname = self.get_sample('sample_applied_on_category_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'categ_id\' field is required.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Category New categ not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'categ_id\' field is required.'), wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'categ_id\' field is required.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Category New categ not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'categ_id\' field is required.'), wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '2_product_category'),
            ('categ_id', '=', self.categ_1_1_1.id),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2), 1)

    def test_import_write_applied_on_category_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_applied_on_category_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'categ_id\' field is required.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Category New categ not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'categ_id\' field is required.'), wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'categ_id\' field is required.'), wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Category New categ not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'categ_id\' field is required.'), wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 4)
        pricelist_items1_base = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 99),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_base), 1)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '2_product_category'),
            ('categ_id', '=', self.categ_1_1_1.id),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'formula'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('pricelist_id', '=', pricelists_1.id),
            ('fixed_price', '=', None),
            ('min_quantity', '=', 0),
            ('percent_price', '=', None),
            ('price_discount', '=', 0.0),
            ('price_max_margin', '=', None),
            ('price_min_margin', '=', None),
            ('price_round', '=', None),
            ('price_surcharge', '=', None),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_create_applied_on_product_tmpl_error(self):
        fname = self.get_sample('sample_applied_on_product_tmpl_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product Template NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product Template NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '1_product'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_write_applied_on_product_tmpl_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_applied_on_product_tmpl_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product Template NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product Template NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_tmpl_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 4)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '1_product'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', self.product_01.product_tmpl_id.id),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'formula'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('pricelist_id', '=', pricelists_1.id),
            ('fixed_price', '=', None),
            ('min_quantity', '=', 0),
            ('percent_price', '=', None),
            ('price_discount', '=', 0.0),
            ('price_max_margin', '=', None),
            ('price_min_margin', '=', None),
            ('price_round', '=', None),
            ('price_surcharge', '=', None),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_sale_import_create_applied_on_product_error(self):
        fname = self.get_sample('sample_applied_on_product_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(
            _('6: The \'product_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '0_product_variant'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', self.product_01.id),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2), 1)

    def test_import_write_applied_on_product_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_applied_on_product_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 5)
        self.assertEquals(len(wizard.line_ids), 3)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 3)
        self.assertIn(_(
            '5: The \'product_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(_(
            '6: Product NEWPROD not found.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '6: The \'product_id\' field is required.'),
            wizard.line_ids[2].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 4)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '0_product_variant'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', self.product_01.id),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'fixed'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', False),
            ('min_quantity', '=', 99),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', False),
            ('price_min_margin', '=', False),
            ('price_round', '=', False),
            ('price_surcharge', '=', False),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_create_compute_price_fixed_error(self):
        fname = self.get_sample('sample_compute_price_fixed_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'fixed_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'fixed_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 2)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2), 1)

    def test_import_write_compute_price_fixed_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_compute_price_fixed_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'fixed_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'fixed_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'formula'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', None),
            ('min_quantity', '=', 0),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', None),
            ('price_min_margin', '=', None),
            ('price_round', '=', None),
            ('price_surcharge', '=', None),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'fixed'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', False),
            ('min_quantity', '=', 99),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', False),
            ('price_min_margin', '=', False),
            ('price_round', '=', False),
            ('price_surcharge', '=', False),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_create_compute_price_percentage_error(self):
        fname = self.get_sample('sample_compute_price_percentage_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'percent_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. '
                'You must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'percent_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. '
                'You must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 2)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'percentage'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 10),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'percentage'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 20),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2), 1)

    def test_import_write_compute_price_percentage_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_compute_price_percentage_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'percent_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. '
                'You must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '3: The \'percent_price\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. '
                'You must choose a valid value.'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'percentage'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 10),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'formula'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', None),
            ('min_quantity', '=', 0),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', None),
            ('price_min_margin', '=', None),
            ('price_round', '=', None),
            ('price_surcharge', '=', None),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'fixed'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', False),
            ('min_quantity', '=', 99),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', False),
            ('price_min_margin', '=', False),
            ('price_round', '=', False),
            ('price_surcharge', '=', False),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'percentage'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 20),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_create_compute_price_formula_error(self):
        fname = self.get_sample('sample_compute_price_formula_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '4: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '7: Pricelist New pricelist not found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '7: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[3].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '4: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '7: Pricelist New pricelist not found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '7: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[3].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 2)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'pricelist'),
            ('base_pricelist_id', '=', self.env.ref('product.list0').id),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2), 1)

    def test_import_write_compute_price_formula_error(self):
        pricelist_1 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_1.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        pricelist_2 = self.env['product.pricelist'].create({
            'name': 'Pricelist test 2',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist_2.id,
            'applied_on': '3_global',
            'min_quantity': 444,
        })
        fname = self.get_sample('sample_compute_price_formula_error.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '4: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '7: Pricelist New pricelist not found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '7: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[3].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 444),
        ])
        self.assertEquals(len(pricelists_item), 1)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 6)
        self.assertEquals(len(wizard.line_ids), 4)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 4)
        self.assertIn(_(
            '4: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[0].name)
        self.assertIn(
            _('5: Option \'False\' for \'compute_price\' does not exist. You '
                'must choose a valid value.'), wizard.line_ids[1].name)
        self.assertIn(_(
            '7: Pricelist New pricelist not found.'), wizard.line_ids[2].name)
        self.assertIn(_(
            '7: The \'base_pricelist_id\' field is required.'),
            wizard.line_ids[3].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'fixed'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', False),
            ('min_quantity', '=', 99),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', False),
            ('price_min_margin', '=', False),
            ('price_round', '=', False),
            ('price_surcharge', '=', False),
            ('pricelist_id', '=', pricelists_1.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 2)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('fixed_price', '=', 0),
            ('percent_price', '=', 0),
            ('base', '=', 'pricelist'),
            ('base_pricelist_id', '=', self.env.ref('product.list0').id),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 1)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '3_global'),
            ('base', '=', 'list_price'),
            ('categ_id', '=', None),
            ('compute_price', '=', 'fixed'),
            ('date_end', '=', None),
            ('date_start', '=', None),
            ('fixed_price', '=', False),
            ('min_quantity', '=', 444),
            ('percent_price', '=', None),
            ('price_discount', '=', 0),
            ('price_max_margin', '=', False),
            ('price_min_margin', '=', False),
            ('price_round', '=', False),
            ('price_surcharge', '=', False),
            ('pricelist_id', '=', pricelists_2.id),
            ('product_id', '=', None),
            ('product_tmpl_id', '=', None),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_write_with_date_columns_multiple_lines_error(self):
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist.id,
            'applied_on': '3_global',
        })
        fname = self.get_sample('sample_with_duplicated_lines.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Multiple pricelist items found'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Multiple pricelist items found'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
        ])
        self.assertEquals(len(pricelists_item), 2)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 3)
        self.assertEquals(len(wizard.line_ids), 2)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 2)
        self.assertIn(_(
            '2: Multiple pricelist items found'), wizard.line_ids[0].name)
        self.assertIn(_(
            '3: Multiple pricelist items found'), wizard.line_ids[1].name)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 80.00),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 0)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)

    def test_import_create_with_date_columns_ok(self):
        fname = self.get_sample('sample_with_date_columns_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 0)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 3)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        self.assertEquals(
            pricelist_items1_1.date_start.strftime('%Y-%m-%d'), '2020-01-01')
        self.assertEquals(
            pricelist_items1_1.date_end.strftime('%Y-%m-%d'), '2020-12-31')
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '2_product_category'),
            ('categ_id', '=', self.categ_1_1_1.id),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 0)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 333),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)

    def test_import_write_with_date_columns_ok(self):
        pricelist = self.env['product.pricelist'].create({
            'name': 'Pricelist test 1',
        })
        self.env['product.pricelist.item'].create({
            'pricelist_id': pricelist.id,
            'applied_on': '3_global',
            'min_quantity': 99,
        })
        fname = self.get_sample('sample_with_date_columns_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        wizard = self.env['import.file'].create({
            'template_id': self.env.ref(
                'import_template_sale_pricelist_item.'
                'template_sale_pricelist_item').id,
            'file': file,
            'file_filename': self.get_file_name(fname),
        })
        wizard.open_template_form()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        pricelists_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('min_quantity', '=', 99),
        ])
        self.assertEquals(len(pricelists_item), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 0)
        wizard.action_import_from_simulation()
        self.assertEquals(wizard.total_rows, 4)
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(wizard.total_warn, 0)
        self.assertEquals(wizard.total_error, 0)
        pricelists_1 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 1'),
        ])
        self.assertEquals(len(pricelists_1), 1)
        self.assertEquals(len(pricelists_1.item_ids), 4)
        pricelist_items1_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 10),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 99.99),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_1), 1)
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '2_product_category'),
            ('categ_id', '=', self.categ_1_1_1.id),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelist_items1_3 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'formula'),
            ('percent_price', '=', None),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', False),
            ('price_round', '=', False),
            ('price_min_margin', '=', False),
            ('price_max_margin', '=', False),
            ('fixed_price', '=', False),
        ])
        self.assertEquals(len(pricelist_items1_3), 1)
        self.assertEquals(
            pricelist_items1_1.date_start.strftime('%Y-%m-%d'), '2020-01-01')
        self.assertEquals(
            pricelist_items1_1.date_end.strftime('%Y-%m-%d'), '2020-12-31')
        pricelist_items1_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_1.id),
            ('applied_on', '=', '2_product_category'),
            ('categ_id', '=', self.categ_1_1_1.id),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 95),
            ('percent_price', '=', 0),
            ('base', '=', 'list_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items1_2), 1)
        pricelists_2 = self.env['product.pricelist'].search([
            ('name', '=', 'Pricelist test 2'),
        ])
        self.assertEquals(len(pricelists_2), 1)
        self.assertEquals(len(pricelists_2.item_ids), 1)
        pricelist_items2_1 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 88),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_1), 0)
        pricelist_items2_2 = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelists_2.id),
            ('applied_on', '=', '3_global'),
            ('categ_id', '=', None),
            ('product_tmpl_id', '=', None),
            ('product_id', '=', None),
            ('min_quantity', '=', 0),
            ('date_start', '=', None),
            ('date_end', '=', None),
            ('compute_price', '=', 'fixed'),
            ('fixed_price', '=', 333),
            ('percent_price', '=', 0),
            ('base', '=', 'standard_price'),
            ('price_discount', '=', 0),
            ('price_surcharge', '=', 0),
            ('price_round', '=', 0),
            ('price_min_margin', '=', 0),
            ('price_max_margin', '=', 0),
        ])
        self.assertEquals(len(pricelist_items2_2), 1)
