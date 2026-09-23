###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestSaleCostSimulatorUpdateQuantity(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test pricelist',
        })
        self.simulator = self.env['sale.cost.simulator'].create({
            'ref': 'SALE-COST-UPDATE-QUANTITY-001',
            'pricelist_id': self.pricelist.id,
            'partner_data': 'Test partner',
        })
        self.parent = self.env['sale.cost.line'].create({
            'name': 'Quantity parent',
            'simulator_id': self.simulator.id,
            'pricelist_id': self.pricelist.id,
        })
        self.child_one = self.env['sale.cost.line'].create({
            'name': 'Quantity child one',
            'simulator_id': self.simulator.id,
            'parent_id': self.parent.id,
            'pricelist_id': self.pricelist.id,
        })
        self.child_two = self.env['sale.cost.line'].create({
            'name': 'Quantity child two',
            'simulator_id': self.simulator.id,
            'parent_id': self.parent.id,
            'pricelist_id': self.pricelist.id,
        })

    def test_default_get_from_line_selects_children(self):
        wizard_model = self.env['sale.cost.update_quantity'].with_context(
            active_model='sale.cost.line', active_id=self.parent.id)
        values = wizard_model.default_get(['line_ids'])
        self.assertEqual(
            values['line_ids'],
            [(6, 0, (self.child_one | self.child_two).ids)])

    def test_default_get_from_simulator_selects_top_level_lines(self):
        wizard_model = self.env['sale.cost.update_quantity'].with_context(
            active_model='sale.cost.simulator', active_id=self.simulator.id)
        values = wizard_model.default_get(['line_ids'])
        self.assertEqual(
            values['line_ids'], [(6, 0, self.simulator.line_ids.ids)])

    def test_button_accept_closes_wizard(self):
        wizard = self.env['sale.cost.update_quantity'].with_context(
            active_model='sale.cost.line', active_id=self.parent.id).create({
                'simulator_id': self.simulator.id,
                'parent_id': self.parent.id,
                'line_ids': [(6, 0, self.child_one.ids)],
            })
        result = wizard.button_accept()
        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
