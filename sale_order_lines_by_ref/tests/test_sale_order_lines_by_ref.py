###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
import os

from odoo import exceptions
from odoo.tests import common


class TestPurchaseOrderInvoiceByRef(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': True,
            'customer': True,
        })
        self.product_1 = self.env['product.product'].create({
            'type': 'service',
            'sale_ok': True,
            'name': 'One',
            'list_price': 10,
            'standard_price': 3,
            'default_code': 'R1',
        })
        self.product_2 = self.env['product.product'].create({
            'type': 'service',
            'sale_ok': True,
            'name': 'Two',
            'list_price': 20,
            'default_code': 'R2',
            'barcode': '0123456789104',
        })

    def create_wizard(self, sale, refs):
        wizard_obj = self.env['sale.order.lines_by_ref'].with_context(
            active_id=sale.id)
        return wizard_obj.create({
            'references': refs,
        })

    def test_sale_order(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(sale, '\n'.join(['R1/10/30.10']))
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 10)
        self.assertEquals(line.price_unit, 30.10)
        sale.order_line.unlink()
        self.assertEquals(len(sale.order_line), 0)
        wizard = self.create_wizard(sale, '\n'.join(['0123456789104/10/20']))
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        line = sale.order_line[0]
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(line.product_id, self.product_2)
        self.assertEquals(line.product_uom_qty, 10)
        self.assertEquals(line.price_unit, 20)
        sale.order_line.unlink()
        wizard = self.create_wizard(sale, '\n'.join(['R1', 'R2']))
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale.order_line), 2)

    def test_sale_order_with_errors(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(sale, 'RXXX/10/30.10')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_create()
        self.assertEquals(len(sale.order_line), 0)

    def test_change_glue_char(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('sale_order_lines_by_ref.glue', ',')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.create_wizard(sale, 'R1,10,30.10')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale.order_line), 1)

    def test_ref_not_for_sale(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.product_1.sale_ok = False
        wizard = self.create_wizard(sale, 'R1')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_create()
        self.assertEquals(len(sale.order_line), 0)

    def get_sample(self, fname):
        return os.path.join(os.path.dirname(__file__), fname)

    def test_import_xlsx_lines_ok(self):
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 8)

    def test_import_xlsx_lines_error_ref_not_exists(self):
        fname = self.get_sample('sample_ref_not_exists.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 0)

    def test_import_xlsx_lines_error_sale_ok_false(self):
        self.product_1.sale_ok = False
        self.assertFalse(self.product_1.sale_ok)
        fname = self.get_sample('sample_sale_ok_false.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 1)
        self.assertEquals('Ref not exists', wizard.line_ids.name)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 0)

    def test_import_xlsx_lines_error_columns_number(self):
        fname = self.get_sample('sample_error_columns_number.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_simulate_import_lines_from_xlsx()
        self.assertEqual(result.exception.name, 'The file must have 3 columns')
        with self.assertRaises(exceptions.ValidationError) as result:
            wizard.action_import_lines_from_xlsx()
        self.assertEqual(result.exception.name, 'The file must have 3 columns')

    def _customer_info_module_installed(self):
        modules = self.env['ir.module.module'].search([
            ('name', '=', 'product_supplierinfo_for_customer_sale'),
            ('state', '=', 'installed'),
        ])
        return modules and True or False

    def _pricelist_formula_margin_module_installed(self):
        modules = self.env['ir.module.module'].search([
            ('name', '=', 'product_pricelist_formula_margin'),
            ('state', '=', 'installed'),
        ])
        return modules and True or False

    def test_import_xlsx_partner_shipping_customerinfo(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': '2323',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 8)

    def test_import_xlsx_partner_shipping_customerinfo_02(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_ends_zero.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': '9128812',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '9128812'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '9128812'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 100)
        self.assertEquals(line.price_unit, 18)

    def test_sale_no_price_xlsx_product_customerinfo_01(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': 'R2323',
            'price': 15,
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 15)

    def test_sale_no_price_xlsx_product_customerinfo_02(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner.id,
            'product_code': 'R2323',
            'price': 15,
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 1)
        self.assertEquals(len(partner_shipping_customerinfo), 0)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 15)

    def test_sale_no_price_xlsx_product_list_price_01(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_2.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(len(sale.order_line), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, self.product_1.list_price)

    def test_sale_no_price_xlsx_product_list_price_02(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_2.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(len(sale.order_line), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, self.product_1.list_price)

    def test_sale_no_price_xlsx_product_price_by_pricelist_01(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_2.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'fixed',
            'fixed_price': 6,
            'product_id': self.product_1.id,
        })
        self.assertEquals(sale.partner_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        self.assertEquals(len(sale.order_line), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, self.pricelist_item.fixed_price)
        self.assertEquals(
            line.price_unit, self.product_1.with_context(
                pricelist=sale.pricelist_id.id).price)

    def test_sale_order_lines_customer(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        product = self.env['product.product'].create({
            'name': 'Product Test',
            'type': 'consu',
            'product_category': self.env.ref('product.product_category_all'),
        })
        self.env['product.customerinfo'].create({
            'product_id': product.id,
            'name': partner.id,
            'product_code': '2323',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        products_customer_code = self.env['product.customerinfo'].search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        wizard = self.create_wizard(sale_order, "2323")
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale_order.order_line), 1)
        self.assertEquals(len(products_customer_code), 1)
        self.assertEquals(len(products_customer_code.product_id), 1)
        self.assertEquals(len(products_customer_code.product_tmpl_id), 0)

    def test_sale_order_lines_same_customer_code_error(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        product = self.env['product.product'].create({
            'name': 'Product Test',
            'type': 'consu',
            'product_category': self.env.ref('product.product_category_all'),
        })
        self.env['product.customerinfo'].create({
            'product_id': product.id,
            'name': partner.id,
            'product_code': '2323',
        })
        self.env['product.customerinfo'].create({
            'product_id': product.id,
            'name': partner.id,
            'product_code': '2323',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        products_customer_code = self.env['product.customerinfo'].search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        wizard = self.create_wizard(sale_order, '2323')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale_order.order_line), 1)
        self.assertEquals(len(products_customer_code), 2)
        self.assertEquals(len(products_customer_code[0].product_id), 1)
        self.assertEquals(len(products_customer_code[0].product_tmpl_id), 0)

    def test_sale_order_lines_customer_product_template(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        product = self.env['product.product'].create({
            'name': 'Product Test',
            'type': 'consu',
            'product_category': self.env.ref('product.product_category_all'),
        })
        self.env['product.customerinfo'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'name': partner.id,
            'product_code': '2323',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        products_customer_code = self.env['product.customerinfo'].search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        wizard = self.create_wizard(sale_order, "2323")
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(sale_order.order_line), 1)
        self.assertEquals(len(products_customer_code), 1)
        self.assertEquals(len(products_customer_code[0].product_id), 0)
        self.assertEquals(len(products_customer_code[0].product_tmpl_id), 1)

    def test_sale_order_lines_customer_product_template_variant_errors(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        product = self.env.ref('product.product_product_4_product_template')
        self.env['product.customerinfo'].create({
            'product_tmpl_id': product.id,
            'name': partner.id,
            'product_code': '2323',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        products_customer_code = self.env['product.customerinfo'].search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        wizard = self.create_wizard(sale_order, "2323")
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 1)
        wizard.action_create()
        self.assertEquals(len(sale_order.order_line), 0)
        self.assertEquals(len(products_customer_code), 1)
        self.assertEquals(len(products_customer_code[0].product_id), 0)
        self.assertEquals(len(
            products_customer_code[0].product_tmpl_id.product_variant_ids),
            products_customer_code[0].product_tmpl_id.product_variant_count)
        self.assertIn('1 variant for', wizard.line_ids[0].name)

    def test_sale_order_lines_customer_product_empty_product(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        self.env['product.customerinfo'].create({
            'name': partner.id,
            'product_code': '2323',
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        products_customer_code = self.env['product.customerinfo'].search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        wizard = self.create_wizard(sale_order, "2323")
        wizard.action_simulate()
        wizard.action_create()
        self.assertEquals(len(sale_order.order_line), 0)
        self.assertEquals(len(products_customer_code), 1)
        self.assertEquals(len(products_customer_code[0].product_id), 0)
        self.assertEquals(len(products_customer_code[0].product_tmpl_id), 0)
        self.assertIn('not exists', wizard.line_ids[0].name)

    def test_sale_order_lines_permission_access(self):
        user = self.env.ref('base.user_demo')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard_obj = self.env['sale.order.lines_by_ref'].sudo(user=user)
        wizard = wizard_obj.with_context(active_id=sale.id).create({
            'references': '2323'
        })
        with self.assertRaises(exceptions.AccessError):
            wizard.action_simulate()
        user.groups_id = [(4, self.env.ref('sales_team.group_sale_manager').id)]
        wizard.action_simulate()

    def test_sale_order_partner_shipping_customerinfo(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        product = self.env['product.product'].create({
            'name': 'Product Test',
            'type': 'consu',
        })
        self.env['product.customerinfo'].create({
            'product_id': product.id,
            'name': partner_shipping.id,
            'product_code': '2323',
        })
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', '2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.create_wizard(sale, '2323')
        wizard.action_simulate()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_create()
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(len(sale.order_line), 1)
        self.assertEquals(sale.order_line[0].product_id, product)

    def test_sale_partner_customerinfo_zero_price(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'fixed',
            'fixed_price': 6,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 1)
        self.assertEquals(len(partner_shipping_customerinfo), 0)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 6)

    def test_sale_partner_customerinfo_price(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner.id,
            'product_code': 'R2323',
            'price': 4,
        })
        self.assertEqual(customerinfo.price, 4)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'fixed',
            'fixed_price': 6,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 1)
        self.assertEquals(len(partner_shipping_customerinfo), 0)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 4)

    def test_sale_partner_shipping_customerinfo_price(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': 'R2323',
            'price': 4,
        })
        self.assertEqual(customerinfo.price, 4)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'fixed',
            'fixed_price': 6,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 4)

    def test_sale_partner_customerinfo_zero_price_pricelist_margin_01(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        if not self._pricelist_formula_margin_module_installed():
            self.skipTest('Module Pricelist Formula Margin Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '3_global',
            'base': 'list_price',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'margin',
            'percent_margin': 40,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 1)
        self.assertEquals(len(partner_shipping_customerinfo), 0)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 5)

    def test_sale_partner_customerinfo_zero_price_pricelist_margin_02(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        if not self._pricelist_formula_margin_module_installed():
            self.skipTest('Module Pricelist Formula Margin Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'list_price',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'margin',
            'percent_margin': 60,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 1)
        self.assertEquals(len(partner_shipping_customerinfo), 0)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 7.5)

    def test_partner_shipping_customerinfo_zero_price_pricelist_margin_03(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        if not self._pricelist_formula_margin_module_installed():
            self.skipTest('Module Pricelist Formula Margin Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '3_global',
            'base': 'list_price',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'margin',
            'percent_margin': 40,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 5)

    def test_partner_shipping_customerinfo_zero_price_pricelist_margin_04(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        if not self._pricelist_formula_margin_module_installed():
            self.skipTest('Module Pricelist Formula Margin Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'list_price',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'margin',
            'percent_margin': 60,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 7.5)

    def test_sale_partner_shipping_customerinfo_zero_price(self):
        if not self._customer_info_module_installed():
            self.skipTest('Module SupplierInfo Not Installed')
        fname = self.get_sample('sample_ok_customerinfo_1.xlsx')
        file = base64.b64encode(open(fname, 'rb').read())
        partner = self.env.ref('base.res_partner_12')
        partner_shipping = self.env['res.partner'].create({
            'name': 'Partner shipping test',
        })
        customerinfo = self.env['product.customerinfo'].create({
            'product_id': self.product_1.id,
            'name': partner_shipping.id,
            'product_code': 'R2323',
        })
        self.assertEqual(customerinfo.price, 0)
        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_shipping_id': partner_shipping.id,
        })
        self.pricelist_item = self.env['product.pricelist.item'].create({
            'applied_on': '1_product',
            'base': 'partner',
            'name': 'Test pricelist item',
            'pricelist_id': sale.pricelist_id.id,
            'compute_price': 'fixed',
            'fixed_price': 6,
            'product_id': self.product_1.id,
        })
        customerinfo_obj = self.env['product.customerinfo']
        partner_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner.id),
        ])
        partner_shipping_customerinfo = customerinfo_obj.search([
            ('product_code', '=', 'R2323'),
            ('name', '=', partner_shipping.id),
        ])
        self.assertEquals(len(partner_customerinfo), 0)
        self.assertEquals(len(partner_shipping_customerinfo), 1)
        self.assertEquals(sale.partner_id, partner)
        self.assertEquals(sale.partner_shipping_id, partner_shipping)
        wizard = self.env['sale.order.lines_by_ref.xlsx'].with_context(
            active_id=sale.id).create({
                'xlsx_file': file,
            })
        wizard.action_simulate_import_lines_from_xlsx()
        self.assertEquals(len(wizard.line_ids), 0)
        wizard.action_import_lines_from_xlsx()
        self.assertEquals(len(sale.order_line), 1)
        line = sale.order_line[0]
        self.assertEquals(line.product_id, self.product_1)
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 6)
