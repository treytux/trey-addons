###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestSaleImportSaleOrderTemplate(TransactionCase):

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
        })
        line_obj = self.env['sale.order.template.line']
        lines_data = [
            {
                'sale_order_template_id': tmpl.id,
                'name': 'line-title%s' % key,
                'display_type': 'line_section',
            },
            {
                'sale_order_template_id': tmpl.id,
                'name': 'line-note%s' % key,
                'display_type': 'line_note',
            },
            {
                'sale_order_template_id': tmpl.id,
                'name': 'line-product%s' % key,
                'product_id': self.product.id,
                'product_uom_qty': 1,
            },
        ]
        line_obj.create(lines_data)
        return tmpl

    def test_sale_import_update(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1')
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda ln: ln.product_id)
        self.assertEqual(len(line), 1)
        line.update({
            'price_unit': 33.33,
            'discount': 11.11,
        })
        self.assertEqual(line.name, 'line-product1')
        self.assertEqual(line.price_unit, 33.33)
        self.assertEqual(line.discount, 11.11)

    def test_sale_import_qty_factor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1')
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.line_ids.write({'qty_factor': 2})
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda ln: ln.product_id)
        self.assertEqual(len(line), 1)
        line.update({
            'price_unit': 33.33,
            'discount': 11.11,
        })
        self.assertEqual(line.name, 'line-product1')
        self.assertEqual(line.product_uom_qty, 2)
        self.assertEqual(line.price_unit, 33.33)
        self.assertEqual(line.discount, 11.11)

    def test_sale_import_price_factor(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        tmpl1 = self.create_sale_template('1')
        wizard = self.env['sale.import.sale.order.template'].create({
            'sale_order_template_ids': [(6, 0, [tmpl1.id])],
        })
        wizard.create_lines()
        wizard.line_ids.write({'price_unit_factor': 2})
        wizard.with_context(active_id=sale.id).select_sale_order_templates()
        line = sale.order_line.filtered(lambda ln: ln.product_id)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.name, 'line-product1')
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.price_unit, 100)

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
        self.assertEqual(len(sale.order_line), 9)
