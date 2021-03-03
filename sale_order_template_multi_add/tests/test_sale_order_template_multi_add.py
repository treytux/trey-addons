###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderTemplateMultiAdd(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_3')
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 50,
            'list_price': 50,
        })

    def create_sale_template(self, key, price_unit=False, discount=False):
        tmpl = self.env['sale.order.template'].create({
            'name': 'template%s' % key,
        })
        line_obj = self.env['sale.order.template.line']
        line_obj.create({
            'sale_order_template_id': tmpl.id,
            'name': 'line-title%s' % key,
            'display_type': 'line_section',
        })
        line_obj.create({
            'sale_order_template_id': tmpl.id,
            'name': 'line-note%s' % key,
            'display_type': 'line_note',
        })
        line_product = line_obj.new({
            'sale_order_template_id': tmpl.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
        })
        line_product._onchange_product_id()
        line_product.update({
            'name': 'line-product%s' % key,
            'price_unit': price_unit,
            'discount': discount,
        })
        line_obj.create(line_obj._convert_to_write(line_product._cache))
        return tmpl

    def test_sale_import_without_update_price(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1', 33.33, 11.11)
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda l: l.product_id)
        self.assertEquals(len(line), 1)
        self.assertEquals(line.name, 'line-product1')
        self.assertEquals(line.price_unit, 33.33)
        self.assertEquals(line.discount, 11.11)

    def test_sale_import_update_price(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1', 33.33, 11.11)
        wizard = self.env['sale.import.sale.order.template'].create({
            'update_price': True,
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda l: l.product_id)
        self.assertEquals(len(line), 1)
        self.assertEquals(line.name, 'line-product1')
        self.assertEquals(line.price_unit, line.product_id.list_price)
        self.assertEquals(line.discount, 0)

    def test_sale_import_qty_factor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1', 33.33, 11.11)
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.line_ids.write({'qty_factor': 2})
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda l: l.product_id)
        self.assertEquals(len(line), 1)
        self.assertEquals(line.name, 'line-product1')
        self.assertEquals(line.product_uom_qty, 2)
        self.assertEquals(line.price_unit, 33.33)
        self.assertEquals(line.discount, 11.11)

    def test_sale_import_price_factor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1', 33.33, 11.11)
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.line_ids.write({'price_unit_factor': 2})
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda l: l.product_id)
        self.assertEquals(len(line), 1)
        self.assertEquals(line.name, 'line-product1')
        self.assertEquals(line.product_uom_qty, 1)
        self.assertEquals(line.price_unit, 66.66)
        self.assertEquals(line.discount, 11.11)

    def test_sale_invoice(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1')
        tmpl2 = self.create_sale_template('2')
        tmpl3 = self.create_sale_template('3')
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [
                (6, 0, [tmpl1.id, tmpl2.id, tmpl3.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        self.assertEquals(len(sale.order_line), 9)

    def test_sale_permission(self):
        user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'groups_id': [(6, 0, [
                self.env.ref('sales_team.group_sale_salesman').id,
            ])],
        })
        tmpl = self.create_sale_template('1')
        wizard_obj = self.env['sale.import.sale.order.template'].sudo(user)
        wizard = wizard_obj.create({
            'sale_order_template_ids': [(6, 0, [tmpl.id])],
        })
        wizard.create_lines()
        wizard.select_sale_order_templates()

    def test_conflict_sale_product_min_quantity_addon(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'sale_product_min_quantity')])
        self.assertTrue(module)
        if module.state != 'installed':
            self.skipTest(
                'Module sale_product_min_quantity not installed')
            return
        tmpl = self.create_sale_template('1')
        self.assertEqual(len(tmpl.sale_order_template_line_ids), 3)
        tmpl_line = tmpl.sale_order_template_line_ids.filtered(
            lambda l: l.product_id)
        tmpl_line.product_id.min_order_qty = 10
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        self.assertEquals(len(sale.order_line), 5)
        with self.assertRaises(UserError):
            self.env['sale.order.line'].create({
                'order_id': sale.id,
                'product_id': tmpl_line.product_id.id,
                'price_unit': 100,
                'product_uom_qty': 1
            })
        self.env['sale.order.line'].create({
            'order_id': sale.id,
            'product_id': tmpl_line.product_id.id,
            'price_unit': 100,
            'product_uom_qty': 10
        })

    def test_product_contract(self):
        module = self.env['ir.module.module'].search([
            ('name', '=', 'product_contract')])
        self.assertTrue(module)
        if module.state != 'installed':
            self.skipTest(
                'Module product_contract not installed')
            return
        contract_template = self.env['contract.template'].create({
            'name': 'Contract Template Test',
        })
        self.product.write({
            'is_contract': True,
            'property_contract_template_id': contract_template.id,
            'recurring_rule_type': 'yearly',
            'default_qty': 2,
        })
        tmpl = self.create_sale_template('1')
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        self.assertEqual(len(tmpl.sale_order_template_line_ids), 3)
        line = sale.order_line.filtered(
            lambda l: l.product_id
        )
        self.assertTrue(line)
        self.assertEqual(
            line.recurring_rule_type,
            line.product_id.recurring_rule_type
        )
        self.assertEqual(
            line.recurring_invoicing_type,
            line.product_id.recurring_invoicing_type
        )
        sale.action_confirm()
        contract = sale.order_line.mapped('contract_id').filtered(
            lambda r: r.active)
        self.assertTrue(contract)
        contract_line = contract.contract_line_ids[0]
        self.assertEqual(
            contract_line.recurring_rule_type,
            contract_line.product_id.recurring_rule_type
        )
        self.assertEqual(
            contract_line.recurring_invoicing_type,
            contract_line.product_id.recurring_invoicing_type
        )
