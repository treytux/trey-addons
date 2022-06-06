###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
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
