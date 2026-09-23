###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestWebsiteRma(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Website RMA Partner',
            'email': 'website-rma@example.com',
        })
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Website RMA Product',
            'detailed_type': 'consu',
            'is_returnable': True,
            'list_price': 100.0,
        })
        cls.product = cls.product_tmpl.product_variant_id
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'partner_invoice_id': cls.partner.id,
            'partner_shipping_id': cls.partner.id,
            'order_line': [
                Command.create({
                    'name': cls.product.name,
                    'product_id': cls.product.id,
                    'product_uom_qty': 1,
                    'product_uom': cls.product.uom_id.id,
                    'price_unit': 100.0,
                }),
            ],
        })

    def test_qty_return_field_exists(self):
        field = self.env['sale.order.line']._fields.get('qty_return')
        self.assertTrue(field)
        self.assertEqual(field.type, 'float')

    def test_address_label_report_render_html(self):
        report = self.env['ir.actions.report']
        html = report._render_qweb_html(
            'website_rma.report_address_label',
            [self.sale_order.id])[0]
        self.assertIn(self.sale_order.name, html.decode())
