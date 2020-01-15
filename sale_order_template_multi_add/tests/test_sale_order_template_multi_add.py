###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
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

    def create_sale_template(self, key):
        tmpl = self.env['sale.order.template'].create({
            'name': 'template%s' % key,
            'title': 'title%s' % key,
            'header_note': 'note%s' % key
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
            'product_uom_qty': 1
        })
        line_product._onchange_product_id()
        line_obj.create(line_obj._convert_to_write(line_product._cache))
        return tmpl

    def test_sale_invoice(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1')
        tmpl2 = self.create_sale_template('2')
        tmpl2.header_note = False
        tmpl3 = self.create_sale_template('3')
        tmpl3.title = False
        tmpl3.header_note = False
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [
                (6, 0, [tmpl1.id, tmpl2.id, tmpl3.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        self.assertEquals(len(sale.order_line), 12)

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
