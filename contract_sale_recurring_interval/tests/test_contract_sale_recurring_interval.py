###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestContractBusinessUnit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.contract_template = self.env['contract.template'].create({
            'name': 'Contract template',
            'contract_type': 'sale',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'name': 'Test product',
            'is_contract': True,
            'contract_template_id': self.contract_template.id,
        })

    def test_sale_order_6_months(self):
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'recurring_interval': 6,
                'recurring_rule_type': 'monthly',
                'name': self.product.name,
                'price_unit': 50.,
                'product_uom_qty': 1})],
        })
        sale.action_confirm()
        contract = sale.order_line.mapped('contract_id')
        self.assertEquals(len(contract), 1)
        line = contract.mapped('contract_line_ids')
        self.assertEquals(line.recurring_interval, 6)
        self.assertEquals(line.recurring_rule_type, 'monthly')
