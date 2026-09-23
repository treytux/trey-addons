###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests import common


class TestStockPickingActionAssignCron(common.TransactionCase):

    def setUp(self):
        super().setUp()
        self.stock_wh = self.env.ref('stock.warehouse0')
        self.main_company = self.env.ref('base.main_company')
        self.company2 = self.env['res.company'].create({
            'name': 'Company test',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'is_company': False,
        })
        self.product_01 = self.env['product.product'].create({
            'type': 'product',
            'company_id': False,
            'name': 'Test product 01',
        })
        self.product_02 = self.env['product.product'].create({
            'type': 'product',
            'company_id': self.company2.id,
            'name': 'Test product 02',
        })
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'user@test.com',
            'company_ids': [(6, 0, [self.main_company.id, self.company2.id])],
            'company_id': self.main_company.id,
            'groups_id': [(6, 0, [
                self.env.ref('base.group_no_one').id,
                self.env.ref('stock.group_stock_user').id,
                self.env.ref('stock.group_stock_multi_warehouses').id,

            ])],
        })

    def create_picking(self, user, warehouse, product, qty=1):
        location_src = warehouse.out_type_id.default_location_src_id
        location_dst = self.env.ref('stock.stock_location_customers')
        return self.env['stock.picking'].with_user(user).create({
            'partner_id': self.partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': location_src.id,
            'location_dest_id': location_dst.id,
            'move_ids': [(0, 0, {
                'product_id': product.id,
                'name': product.name,
                'product_uom': product.uom_id.id,
                'product_uom_qty': qty,
                'location_id': location_src.id,
                'location_dest_id': location_dst.id,
            })]
        })

    def update_qty_on_hand(self, product, location, new_qty):
        self.env['stock.quant']._update_available_quantity(
            product, location, new_qty)
        self.assertEqual(
            self.env['stock.quant']._get_available_quantity(product, location),
            new_qty)

    def test_action_assign_cron(self):
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        picking = self.create_picking(
            self.user, self.stock_wh, self.product_01)
        self.assertEqual(picking.state, 'draft')
        picking.with_user(self.user).action_confirm()
        self.assertEqual(picking.state, 'confirmed')
        picking.with_user(self.user).action_assign()
        self.assertEqual(picking.state, 'confirmed')
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 10)
        self.env['stock.picking']._action_assign_cron()
        self.assertEqual(picking.state, 'assigned')

    def test_action_assign_cron_multicompany(self):
        self.assertEqual(self.product_01.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        self.assertEqual(self.product_02.with_context(
            location=self.stock_wh.lot_stock_id.id).qty_available, 0)
        wh_company2 = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company2.id),
        ])
        picking_company1 = self.create_picking(
            self.user, self.stock_wh, self.product_01)
        self.assertEqual(picking_company1.state, 'draft')
        picking_company1.with_user(self.user).action_confirm()
        self.assertEqual(picking_company1.state, 'confirmed')
        picking_company1.with_user(self.user).action_assign()
        self.assertEqual(picking_company1.state, 'confirmed')
        self.user.company_id = self.company2.id
        picking_company2 = self.create_picking(
            self.user, wh_company2, self.product_02)
        self.assertEqual(picking_company2.state, 'draft')
        picking_company2.with_user(self.user).action_confirm()
        self.assertEqual(picking_company2.state, 'confirmed')
        picking_company2.with_user(self.user).action_assign()
        self.assertEqual(picking_company2.state, 'confirmed')
        self.update_qty_on_hand(
            self.product_01, self.stock_wh.lot_stock_id, 10)
        self.update_qty_on_hand(
            self.product_02, wh_company2.lot_stock_id, 10)
        self.env['stock.picking']._action_assign_cron()
        self.assertEqual(picking_company1.state, 'assigned')
        self.assertEqual(picking_company2.state, 'assigned')
