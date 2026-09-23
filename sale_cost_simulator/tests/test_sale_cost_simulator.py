##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleCostSimulator(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'email': 'test@example.com',
        })
        self.pricelist = self.env['product.pricelist'].create({
            'name': 'Test Pricelist',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'lst_price': 100.0,
        })
        self.simulator = self.env['sale.cost.simulator'].create({
            'ref': 'SIM-2026-001',
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'partner_data': 'Test Partner Data',
        })

    def test_state_workflow(self):
        self.assertEqual(self.simulator.state, 'draft')
        self.simulator.to_send()
        self.assertEqual(self.simulator.state, 'send')
        self.simulator.to_done()
        self.assertEqual(self.simulator.state, 'done')
        self.simulator.to_cancel()
        self.assertEqual(self.simulator.state, 'cancel')
        self.simulator.to_draft()
        self.assertEqual(self.simulator.state, 'draft')

    def test_line_hierarchy_and_totals(self):
        line_parent = self.env['sale.cost.line'].create({
            'name': 'Parent Line',
            'simulator_id': self.simulator.id,
            'product_id': self.product.id,
            'quantity': 2.0,
            'price_unit': 50.0,
        })
        line_child = self.env['sale.cost.line'].create({
            'name': 'Child Line',
            'simulator_id': self.simulator.id,
            'parent_id': line_parent.id,
            'product_id': self.product.id,
            'quantity': 1.0,
            'price_unit': 30.0,
        })
        self.simulator.compute_total()
        self.assertEqual(line_parent.level, 1)
        self.assertEqual(line_child.level, 2)
        self.assertEqual(line_parent.childs_number, 1)
        self.assertEqual(line_parent.amount_untaxed, 100.0)
        self.assertEqual(line_child.amount_untaxed, 30.0)
        self.assertEqual(line_parent.total_untaxed, 130.0)
        self.assertEqual(self.simulator.amount_untaxed, 130.0)

    def test_unique_ref_constraint(self):
        with self.assertRaises(ValidationError):
            self.env['sale.cost.simulator'].create({
                'ref': 'SIM-2026-001',
                'partner_id': self.partner.id,
                'pricelist_id': self.pricelist.id,
                'partner_data': 'Duplicate Data',
            })

    def test_cross_reference_constraint(self):
        line = self.env['sale.cost.line'].create({
            'name': 'Self referencing line',
            'simulator_id': self.simulator.id,
        })
        with self.assertRaises(ValidationError):
            line.write({
                'parent_id': line.id,
            })

    def test_simulator_copy_recursive(self):
        line_parent = self.env['sale.cost.line'].create({
            'name': 'Parent Line',
            'simulator_id': self.simulator.id,
        })
        self.env['sale.cost.line'].create({
            'name': 'Child Line',
            'simulator_id': self.simulator.id,
            'parent_id': line_parent.id,
        })
        copied_simulator = self.simulator.copy()
        self.assertIn('(copy)', copied_simulator.ref)
        self.assertEqual(len(copied_simulator.line_ids), 1)
        self.assertEqual(len(copied_simulator.line_ids.child_ids), 1)

    def test_onchange_partner(self):
        simulator_new = self.env['sale.cost.simulator'].new({
            'partner_id': self.partner.id,
        })
        simulator_new._onchange_partner_id()
        self.assertTrue(simulator_new.partner_data)
        self.assertIn('Test Partner', simulator_new.partner_data)
