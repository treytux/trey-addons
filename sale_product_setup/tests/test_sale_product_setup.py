###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleProductSetup(TransactionCase):

    def test_setup_line_quantity(self):
        product_tmpl = self.env.ref('sale_product_setup.setup_product')
        categ = self.env.ref('sale_product_setup.categ_chasis')
        line = self.env['product.setup.line'].create({
            'product_tmpl_id': product_tmpl.id,
            'name': product_tmpl.name,
            'categ_id': categ.id,
            'quantity_min': 10.0,
        })
        self.assertEqual(line.name, product_tmpl.name)
        self.assertEqual(line.quantity_min, 10)
        self.assertEqual(line.quantity_max, 1)
        line.onchange_quantity()
        self.assertEqual(line.quantity_max, 10)
        line.quantity_min = 100
        line.onchange_quantity()
        self.assertEqual(line.quantity_max, 100)
        line.quantity_min = 1
        line.onchange_quantity()
        self.assertEqual(line.quantity_max, 100)

    def test_setup_category(self):
        categ = self.env.ref('sale_product_setup.categ_chasis')
        self.assertEquals(categ.product_template_count, 0)
        categ.write({
            'product_tmpl_ids': [(6, 0, [
                self.env.ref(
                    'sale_product_setup.component_intel_xeon_2637').id,
                self.env.ref(
                    'sale_product_setup.component_intel_xeon_2623').id])]
        })
        self.assertEquals(categ.product_template_count, 2)

    def test_product_setup_option(self):
        product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        product2 = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product 2',
            'standard_price': 10,
            'list_price': 100,
        })
        product_option = self.env['product.setup.option'].create({
            'product_id': product.id,
            'quantity': 1,
        })
        self.assertFalse(product_option.name)
        product_option.product_id = product2.id
        product_option.onchange_product_id()
        self.assertEquals(product_option.name, product_option.product_id.name)

    def test_check_setup_categ_id(self):
        pr_template = self.env.ref(
            'sale_product_setup.component_intel_xeon_2637')
        pr_template.check_setup_categ_id()
        pr_template.write({
            'setup_property_ids': [(4, self.env.ref(
                'sale_product_setup.property_ram_ddr3').id)]
        })
        with self.assertRaises(UserError):
            pr_template.check_setup_categ_id()

    def test_compute_setup_product_ids(self):
        pr_template = self.env.ref(
            'sale_product_setup.component_intel_xeon_2623')
        pr_template.is_setup = True
        self.assertFalse(pr_template.setup_product_ids)
        pr_template.setup_ids = self.env.ref(
            'sale_product_setup.setup_product_processors_line')
        self.assertEquals(
            pr_template.setup_product_ids,
            pr_template.setup_ids.mapped(
                'categ_id.product_tmpl_ids.product_variant_ids'))
        self.assertEquals(
            pr_template.setup_product_count,
            len(pr_template.setup_ids.mapped(
                'categ_id.product_tmpl_ids.product_variant_ids')))

    def test_sale_product_setup(self):
        pr_template = self.env.ref(
            'sale_product_setup.component_intel_xeon_2623')
        pr_template.setup_ids = self.env.ref(
            'sale_product_setup.setup_product_processors_line')
        wizard = self.env['sale.product_setup'].create({
            'product_tmpl_id': pr_template.id,
        })
        self.assertFalse(wizard.line_ids)
        wizard.create_lines()
        self.assertTrue(wizard.line_ids)
        sale_product_setup_line = wizard.line_ids[0]
        self.assertEquals(sale_product_setup_line.wizard_id, wizard)
        self.assertEquals(sale_product_setup_line.setup_id, wizard)
        self.assertEquals(
            sale_product_setup_line.name,
            wizard.product_tmpl_id.setup_ids[0].name)
        self.assertEquals(
            sale_product_setup_line.categ_id,
            wizard.product_tmpl_id.setup_ids[0].categ_id)
