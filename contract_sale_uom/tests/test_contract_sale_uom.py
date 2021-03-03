###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestContractSaleUom(TransactionCase):

    def setUp(self):
        super().setUp()
        self.uom_annual = self.env.ref('contract_sale_uom.uom_annual')
        self.uom_monthly = self.env.ref('contract_sale_uom.uom_monthly')
        self.uom_semester = self.env.ref('contract_sale_uom.uom_semester')
        self.uom_quarter = self.env.ref('contract_sale_uom.uom_quarter')
        self.uom_trimester = self.env.ref('contract_sale_uom.uom_trimester')
        self.contract_template = self.env['contract.template'].create({
            'name': 'Contract template',
            'contract_type': 'sale',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
            'is_contract': True,
            'uom_id': self.uom_annual.id,
            'uom_po_id': self.uom_annual.id,
            'contract_template_id': self.contract_template.id,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })

    def test_data_uom(self):
        self.assertEquals(self.uom_annual.factor_inv, 12)
        self.assertEquals(self.uom_monthly.factor_inv, 1)
        self.assertEquals(
            self.uom_annual._compute_quantity(1, self.uom_monthly), 12)
        self.assertEquals(
            self.uom_monthly._compute_quantity(12, self.uom_annual), 1)
        self.assertEquals(
            self.uom_semester._compute_quantity(1, self.uom_monthly), 6)
        self.assertEquals(
            self.uom_quarter._compute_quantity(1, self.uom_monthly), 4)
        self.assertEquals(
            self.uom_trimester._compute_quantity(1, self.uom_monthly), 3)

    def test_sale_contract_uom_not_required(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 1200,
                    'product_uom_qty': 1,
                    'product_uom': self.uom_annual.id,
                    'contract_quantity': 2,
                }),
            ]
        })
        sale.action_confirm()
        line = sale.mapped('order_line.contract_id.contract_line_ids')
        self.assertEquals(len(line), 1)
        self.assertEquals(line.uom_id, self.uom_annual)

    def test_sale_contract_uom(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'price_unit': 1200,
                    'product_uom_qty': 1,
                    'product_uom': self.uom_annual.id,
                    'contract_quantity': 2,
                    'contract_uom_id': self.uom_monthly.id,
                }),
            ]
        })
        sale.action_confirm()
        line = sale.mapped('order_line.contract_id.contract_line_ids')
        self.assertEquals(len(line), 1)
        self.assertEquals(line.uom_id, self.uom_monthly)
        self.assertEquals(line.quantity, 2)
        self.assertEquals(line.price_unit, 200)

    def test_sale_onchange(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        line_obj = self.env['sale.order.line']
        line = line_obj.new({
            'order_id': sale.id,
            'product_id': self.product.id,
            'price_unit': 1200,
            'product_uom_qty': 1,
            'product_uom': self.uom_annual.id,
        })
        line.product_id_change()
        self.assertEquals(line.contract_quantity, line.product_uom_qty)
        self.assertEquals(line.contract_uom_id, line.product_uom)
        line.product_uom_qty = 2
        self.assertNotEqual(line.contract_quantity, line.product_uom_qty)
        line.product_uom_change()
        self.assertEquals(line.contract_quantity, line.product_uom_qty)
        line.product_uom = self.uom_monthly.id
        self.assertNotEqual(line.contract_uom_id, line.product_uom)
        line.product_uom_change()
        self.assertEquals(line.contract_uom_id, line.product_uom)

    def test_sale_add_section(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'display_type': 'line_section',
                    'name': 'Test section line',
                }),
            ]
        })
        sale.action_confirm()
        self.assertEquals(len(sale.order_line), 1)
