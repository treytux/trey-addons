###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.addons.contract_sale_generation.tests.common import \
    ContractSaleCommon
from odoo.tests.common import TransactionCase


class TestContractSaleGenerationRoute(ContractSaleCommon, TransactionCase):

    def setUp(self):
        super().setUp()
        self.route = self.env['stock.route'].create({
            'name': 'Contract sale test route',
            'sale_selectable': True,
            'company_id': self.env.company.id,
        })

    def test_route_is_copied_to_generated_sale_line(self):
        self.contract_line.route_id = self.route
        sale = self.contract.recurring_create_sale()
        self.assertEqual(sale.order_line.mapped('route_id'), self.route)

    def test_route_is_not_added_when_contract_line_is_empty(self):
        sale = self.contract.recurring_create_sale()
        self.assertFalse(sale.order_line.mapped('route_id'))

    def test_route_field_tracks_contract_generation_type(self):
        self.assertEqual(self.contract_line.contract_generation_type, 'sale')
        self.contract.generation_type = 'invoice'
        self.assertEqual(
            self.contract_line.contract_generation_type, 'invoice')
