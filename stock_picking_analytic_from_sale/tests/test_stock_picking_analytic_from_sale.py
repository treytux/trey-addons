###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.fields import Command
from odoo.tests.common import TransactionCase


class TestStockPickingAnalyticFromSale(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context={**cls.env.context, 'tracking_disable': True})
        cls.plan = cls.env['account.analytic.plan'].create({
            'name': 'Test Plan',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
            'standard_price': 25.0,
            'categ_id': cls.env.ref('product.product_category_all').id,
        })
        cls.product.categ_id.write({
            'property_valuation': 'real_time',
            'property_cost_method': 'average',
        })
        cls.partner = cls.env.ref('base.res_partner_1')

    def _create_sale_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 3,
                'price_unit': 100.0,
            })],
        })

    def _validate_picking(self, picking):
        for move in picking.move_ids:
            move.quantity_done = move.product_uom_qty
        picking.button_validate()

    def test_01_autocreate_and_propagate(self):
        so = self._create_sale_order()
        account = self.env['account.analytic.account'].create({
            'name': so.name,
            'plan_id': self.plan.id,
        })
        so.analytic_account_id = account
        so.action_confirm()
        self.assertTrue(so.analytic_account_id)
        picking = so.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing'
        )
        self.assertTrue(picking)
        self.assertEqual(picking.analytic_account_id, so.analytic_account_id)
        self._validate_picking(picking)
        lines = self.env['account.analytic.line'].search([
            ('account_id', '=', so.analytic_account_id.id),
        ])
        self.assertTrue(lines)
        for line in lines:
            self.assertEqual(line.stock_move_id.picking_id, picking)

    def test_02_no_analytic_account(self):
        so = self._create_sale_order()
        so.action_confirm()
        self.assertFalse(so.analytic_account_id)
        for picking in so.picking_ids:
            self.assertFalse(picking.analytic_account_id)

    def test_03_already_done_picking(self):
        so = self._create_sale_order()
        so.action_confirm()
        picking = so.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing'
        )
        self._validate_picking(picking)
        self.assertFalse(picking.analytic_account_id)
        lines_before = self.env['account.analytic.line'].search([
            ('stock_move_id', 'in', picking.move_ids.ids),
        ])
        self.assertFalse(lines_before)
        account = self.env['account.analytic.account'].create({
            'name': so.name,
            'plan_id': self.plan.id,
        })
        so.analytic_account_id = account
        so._propagate_analytic_to_pickings()
        self.assertEqual(picking.analytic_account_id, account)
        lines_after = self.env['account.analytic.line'].search([
            ('account_id', '=', account.id),
        ])
        self.assertTrue(lines_after)

    def test_04_force_wizard(self):
        so = self._create_sale_order()
        so.action_confirm()
        picking = so.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing'
        )
        self._validate_picking(picking)
        self.assertFalse(picking.analytic_account_id)
        account = self.env['account.analytic.account'].create({
            'name': 'Forced Account',
            'plan_id': self.plan.id,
        })
        wizard = self.env['stock.move.analytic.create'].create({
            'picking_id': picking.id,
            'analytic_account_id': account.id,
        })
        wizard.action_create_analytic()
        self.assertEqual(picking.analytic_account_id, account)
        lines = self.env['account.analytic.line'].search([
            ('account_id', '=', account.id),
        ])
        self.assertTrue(lines)

    def test_05_sale_order_name_in_analytic_line(self):
        so = self._create_sale_order()
        account = self.env['account.analytic.account'].create({
            'name': so.name,
            'plan_id': self.plan.id,
        })
        so.analytic_account_id = account
        so.action_confirm()
        picking = so.picking_ids.filtered(
            lambda p: p.picking_type_code == 'outgoing'
        )
        self._validate_picking(picking)
        lines = self.env['account.analytic.line'].search([
            ('account_id', '=', so.analytic_account_id.id),
        ])
        for line in lines:
            self.assertIn(so.name, line.name)
