###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestStockPickingPrepareUserWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test company'
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'service',
            'company_id': False,
            'name': 'Service product',
            'standard_price': 10,
            'list_price': 100,
        })
        self.warehouse = self.env.ref('stock.warehouse0')
        self.customer_loc = self.env.ref('stock.stock_location_customers')
        self.picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.warehouse.out_type_id.default_location_src_id.id,
            'location_dest_id': self.customer_loc.id,
            'move_lines': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom': self.product.uom_id.id,
                    'product_uom_qty': 1,
                }),
            ],
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.company.id])],
            'company_id': self.company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
            ])],
        })

    def test_raise_wizard(self):
        wizard = self.env['stock.picking.prepare_user'].with_context({
            'active_id': self.picking.id,
        }).create({})
        with self.assertRaises(Exception):
            wizard.action_assign_prepare_user()

    def test_wizard(self):
        self.assertFalse(self.picking.user_id)
        self.assertEqual(self.picking.picking_type_code, 'outgoing')
        self.assertEquals(self.picking.state, 'draft')
        wizard = self.env['stock.picking.prepare_user'].with_context({
            'active_id': self.picking.id,
        }).create({
            'picking_id': self.picking.id,
            'user_id': self.user.id,
        })
        wizard.action_assign_prepare_user()
        self.assertEquals(self.picking.user_id, self.user)
