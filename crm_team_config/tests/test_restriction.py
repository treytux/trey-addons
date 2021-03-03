###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestRestriction(TransactionCase):

    def setUp(self):
        super(TestRestriction, self).setUp()
        self.journal_sale = self.env['account.journal'].search([
            ('type', '=', 'sale')], limit=1)
        if not self.journal_sale:
            raise UserError(_('There is no account journal of sale type.'))
        self.check_journal = self.env['account.journal'].create({
            'name': 'Received check',
            'type': 'bank',
            'code': 'CHK',
        })
        self.check_journal2 = self.env['account.journal'].create({
            'name': 'Received check2',
            'type': 'bank',
            'code': 'CHK2',
        })
        self.sale_journal = self.env['account.journal'].create({
            'name': 'Customer inv',
            'type': 'sale',
            'code': 'INV',
        })
        self.sale_journal2 = self.env['account.journal'].create({
            'name': 'Customer inv2',
            'type': 'sale',
            'code': 'INV2',
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner test',
        })
        self.product = self.env['product.product'].create({
            'type': 'product',
            'name': 'Product test',
            'standard_price': 10,
            'list_price': 100,
        })
        self.user_warehouse = self.env['res.users'].create({
            'name': 'User warehouse',
            'login': 'user_warehouse@test.com',
            'groups_id': [
                (4, self.env.ref('stock.group_stock_user').id),
                (4, self.env.ref('stock.group_stock_multi_warehouses').id),
                (4, self.env.ref('account.group_account_invoice').id),
                (4, self.env.ref('crm_team_config.group_my_crm_team').id)]
        })
        self.manager_warehouse = self.env['res.users'].create({
            'name': 'Manager warehouse',
            'login': 'manager_warehouse@test.com',
            'groups_id': [
                (4, self.env.ref('stock.group_stock_manager').id),
                (4, self.env.ref('stock.group_stock_multi_warehouses').id),
                (4, self.env.ref('account.group_account_invoice').id)],
        })
        self.manager_wh_salesman = self.env['res.users'].create({
            'name': 'Manager warehouse salesman',
            'login': 'manager_wh_salesman@test.com',
            'groups_id': [
                (4, self.env.ref('sales_team.group_sale_manager').id),
                (4, self.env.ref('stock.group_stock_multi_locations').id),
                (4, self.env.ref('stock.group_stock_multi_warehouses').id),
                (4, self.env.ref('stock.group_stock_manager').id)],
        })
        self.warehouse1 = self.create_warehouse('1')
        self.picking1 = self.create_picking(self.warehouse1)
        self.warehouse2 = self.create_warehouse('2')
        self.picking2 = self.create_picking(self.warehouse2)
        self.orderpoint_wh1 = self.create_orderpoint('1', self.warehouse1)
        self.orderpoint_wh2 = self.create_orderpoint('2', self.warehouse2)
        self.inventory_wh1 = self.create_inventory('1', self.warehouse1)
        self.inventory_wh2 = self.create_inventory('2', self.warehouse2)

    def create_crm_team(
            self, key, warehouses=None, payment_journals=None,
            invoice_journals=None):
        data = {
            'name': 'Crm team %s' % key,
        }
        if warehouses:
            data.update({'warehouse_ids': [(6, 0, warehouses.ids)]})
        if payment_journals:
            data.update({
                'payment_journal_ids': [(6, 0, payment_journals.ids)]})
        if invoice_journals:
            data.update({
                'invoice_journal_ids': [(6, 0, invoice_journals.ids)]})
        return self.env['crm.team'].create(data)

    def create_warehouse(self, key):
        return self.env['stock.warehouse'].create({
            'name': 'Warehouse %s' % key,
            'code': 'WH%s' % key,
        })

    def create_picking(self, warehouse):
        location_def = warehouse.out_type_id.default_location_src_id
        return self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': warehouse.out_type_id.id,
            'location_id': location_def.id,
            'location_dest_id': location_def.id,
            'move_lines': [(0, 0, {
                'product_id': self.product.id,
                'name': self.product.name,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 10})]
        })

    def create_orderpoint(self, key, warehouse):
        return self.env['stock.warehouse.orderpoint'].create({
            'name': 'Orderpoint %s' % key,
            'product_id': self.product.id,
            'warehouse_id': warehouse.id,
            'location_id': warehouse.out_type_id.default_location_src_id.id,
            'product_min_qty': 5,
            'product_max_qty': 20,
        })

    def create_inventory(self, key, warehouse):
        location = warehouse.out_type_id.default_location_src_id
        inventory = self.env['stock.inventory'].create({
            'name': 'Inventory %s' % key,
            'filter': 'product',
            'location_id': location.id,
            'product_id': self.product.id,
            'exhausted': True,
        })
        inventory.action_start()
        inventory.line_ids.write({
            'product_qty': 10,
            'location_id': location.id,
        })
        inventory._action_done()
        return inventory

    def test_check_access_warehouse_01(self):
        self.warehouse1.sudo(
            self.manager_warehouse).browse(self.warehouse1.id).name
        with self.assertRaises(AccessError):
            self.warehouse1.sudo(
                self.user_warehouse).browse(self.warehouse1.id).name

    def test_check_access_warehouse_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.warehouse1.sudo(
            self.user_warehouse).browse(self.warehouse1.id).name
        self.warehouse1.sudo(
            self.manager_warehouse).browse(self.warehouse1.id).name

    def test_check_access_warehouse_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.warehouse2.sudo(
                self.user_warehouse).browse(self.warehouse2.id).name
        self.warehouse2.sudo(self.manager_warehouse).browse(
            self.warehouse2.id).name

    def test_check_access_picking_type_01(self):
        self.warehouse1.out_type_id.sudo(self.manager_warehouse).browse(
            self.warehouse1.out_type_id.id).name
        with self.assertRaises(AccessError):
            self.warehouse1.out_type_id.sudo(self.user_warehouse).browse(
                self.warehouse1.out_type_id.id).name

    def test_check_access_picking_type_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.warehouse1.out_type_id.sudo(self.user_warehouse).browse(
            self.warehouse1.out_type_id.id).name
        self.warehouse1.out_type_id.sudo(self.manager_warehouse).browse(
            self.warehouse1.out_type_id.id).name

    def test_check_access_picking_type_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.warehouse2.out_type_id.sudo(self.user_warehouse).browse(
                self.warehouse2.out_type_id.id).name
        self.warehouse2.out_type_id.sudo(self.manager_warehouse).browse(
            self.warehouse2.out_type_id.id).name

    def test_check_access_picking_01(self):
        self.picking1.sudo(
            self.manager_warehouse).browse(self.picking1.id).name
        with self.assertRaises(AccessError):
            self.picking1.sudo(
                self.user_warehouse).browse(self.picking1.id).name

    def test_check_access_picking_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.picking1.sudo(self.user_warehouse).browse(self.picking1.id).name
        self.picking1.sudo(self.manager_warehouse).browse(
            self.picking1.id).name

    def test_check_access_picking_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.picking2.sudo(
                self.user_warehouse).browse(self.picking2.id).name
        self.picking2.sudo(self.manager_warehouse).browse(
            self.picking2.id).name

    def test_check_access_orderpoint_01(self):
        self.orderpoint_wh1.sudo(
            self.manager_warehouse).browse(self.orderpoint_wh1.id).name
        with self.assertRaises(AccessError):
            self.orderpoint_wh1.sudo(
                self.user_warehouse).browse(self.orderpoint_wh1.id).name

    def test_check_access_orderpoint_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.orderpoint_wh1.sudo(self.user_warehouse).browse(
            self.orderpoint_wh1.id).name
        self.orderpoint_wh1.sudo(self.manager_warehouse).browse(
            self.orderpoint_wh1.id).name

    def test_check_access_orderpoint_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.orderpoint_wh2.sudo(
                self.user_warehouse).browse(self.orderpoint_wh2.id).name
        self.orderpoint_wh2.sudo(self.manager_warehouse).browse(
            self.orderpoint_wh2.id).name

    def test_check_access_location_01(self):
        location_wh1 = self.warehouse1.out_type_id.default_location_src_id
        location_wh1.sudo(self.manager_warehouse).browse(location_wh1.id).name
        with self.assertRaises(AccessError):
            location_wh1.sudo(self.user_warehouse).browse(location_wh1.id).name

    def test_check_access_location_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        location_wh1 = self.warehouse1.out_type_id.default_location_src_id
        location_wh1.sudo(self.user_warehouse).browse(
            location_wh1.id).name
        location_wh1.sudo(self.manager_warehouse).browse(
            location_wh1.id).name

    def test_check_access_location_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        location_wh2 = self.warehouse2.out_type_id.default_location_src_id
        with self.assertRaises(AccessError):
            location_wh2.sudo(self.user_warehouse).browse(location_wh2.id).name
        location_wh2.sudo(self.manager_warehouse).browse(location_wh2.id).name

    def test_check_access_inventory_01(self):
        self.inventory_wh1.sudo(self.manager_warehouse).browse(
            self.inventory_wh1.id).name
        with self.assertRaises(AccessError):
            self.inventory_wh1.sudo(self.user_warehouse).browse(
                self.inventory_wh1.id).name

    def test_check_access_inventory_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.inventory_wh1.sudo(self.user_warehouse).browse(
            self.inventory_wh1.id).name
        self.inventory_wh1.sudo(self.manager_warehouse).browse(
            self.inventory_wh1.id).name

    def test_check_access_inventory_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.inventory_wh2.sudo(self.user_warehouse).browse(
                self.inventory_wh2.id).name
        self.inventory_wh2.sudo(self.manager_warehouse).browse(
            self.inventory_wh2.id).name

    def test_check_access_inventory_line_01(self):
        self.inventory_wh1.line_ids[0].sudo(self.manager_warehouse).browse(
            self.inventory_wh1.line_ids[0].id).product_id
        with self.assertRaises(AccessError):
            self.inventory_wh1.line_ids[0].sudo(self.user_warehouse).browse(
                self.inventory_wh1.line_ids[0].id).product_id

    def test_check_access_inventory_line_02(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        self.inventory_wh1.line_ids[0].sudo(self.user_warehouse).browse(
            self.inventory_wh1.line_ids[0].id).product_id
        self.inventory_wh1.line_ids[0].sudo(self.manager_warehouse).browse(
            self.inventory_wh1.line_ids[0].id).product_id

    def test_check_access_inventory_line_03(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        self.assertEqual(crm_team1.warehouse_ids[0], self.warehouse1)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.warehouse1, self.user_warehouse.sale_team_id.warehouse_ids)
        with self.assertRaises(AccessError):
            self.inventory_wh2.line_ids[0].sudo(self.user_warehouse).browse(
                self.inventory_wh2.line_ids[0].id).product_id
        self.inventory_wh2.line_ids[0].sudo(self.manager_warehouse).browse(
            self.inventory_wh2.line_ids[0].id).product_id

    def test_check_access_account_journal_01(self):
        self.check_journal.sudo(
            self.manager_warehouse).browse(self.check_journal.id).name
        with self.assertRaises(AccessError):
            self.check_journal.sudo(
                self.user_warehouse).browse(self.check_journal.id).name

    def test_check_access_account_journal_02(self):
        crm_team1 = self.create_crm_team(
            '1', self.warehouse1, payment_journals=self.check_journal)
        self.assertEqual(crm_team1.payment_journal_ids[0], self.check_journal)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.check_journal,
            self.user_warehouse.sale_team_id.payment_journal_ids)
        self.check_journal.sudo(
            self.user_warehouse).browse(self.check_journal.id).name
        self.check_journal.sudo(
            self.manager_warehouse).browse(self.check_journal.id).name

    def test_check_access_account_journal_03(self):
        crm_team1 = self.create_crm_team(
            '1', self.warehouse1, payment_journals=self.check_journal)
        self.assertEqual(crm_team1.payment_journal_ids[0], self.check_journal)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.check_journal,
            self.user_warehouse.sale_team_id.payment_journal_ids)
        with self.assertRaises(AccessError):
            self.check_journal2.sudo(
                self.user_warehouse).browse(self.check_journal2.id).name
        self.check_journal2.sudo(self.manager_warehouse).browse(
            self.check_journal2.id).name

    def test_check_access_invoice_journal_01(self):
        self.sale_journal.sudo(
            self.manager_warehouse).browse(self.sale_journal.id).name
        with self.assertRaises(AccessError):
            self.sale_journal.sudo(
                self.user_warehouse).browse(self.sale_journal.id).name

    def test_check_access_invoice_journal_02(self):
        crm_team1 = self.create_crm_team(
            '1', self.warehouse1, invoice_journals=self.sale_journal)
        self.assertEqual(
            crm_team1.invoice_journal_ids[0], self.sale_journal)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.sale_journal,
            self.user_warehouse.sale_team_id.invoice_journal_ids)
        self.sale_journal.sudo(
            self.user_warehouse).browse(self.sale_journal.id).name
        self.sale_journal.sudo(
            self.manager_warehouse).browse(self.sale_journal.id).name

    def test_check_access_invoice_journal_03(self):
        crm_team1 = self.create_crm_team(
            '1', self.warehouse1, invoice_journals=self.sale_journal)
        self.assertEqual(crm_team1.invoice_journal_ids[0], self.sale_journal)
        crm_team1.member_ids = [(6, 0, [self.user_warehouse.id])]
        self.assertIn(self.user_warehouse, crm_team1.member_ids)
        self.assertIn(
            self.sale_journal,
            self.user_warehouse.sale_team_id.invoice_journal_ids)
        with self.assertRaises(AccessError):
            self.sale_journal2.sudo(
                self.user_warehouse).browse(self.sale_journal2.id).name
        self.sale_journal2.sudo(self.manager_warehouse).browse(
            self.sale_journal2.id).name

    def test_check_update_locations_when_create_location_01(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        location_default = self.warehouse1.out_type_id.default_location_src_id
        self.assertIn(location_default, crm_team1.location_ids)
        location_test = self.env['stock.location'].sudo(
            self.manager_wh_salesman).create({
                'name': 'Location test',
                'location_id': location_default.location_id.id,
            })
        self.assertIn(location_default, crm_team1.location_ids)
        self.assertIn(location_test, crm_team1.location_ids)

    def test_check_update_locations_when_write_location_01(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        location_def_wh1 = self.warehouse1.out_type_id.default_location_src_id
        self.assertIn(location_def_wh1, crm_team1.location_ids)
        location_def_wh2 = self.warehouse2.out_type_id.default_location_src_id
        location_def_wh1.location_id = location_def_wh2
        crm_team2 = self.create_crm_team('2', self.warehouse2)
        self.assertNotIn(location_def_wh1, crm_team1.location_ids)
        self.assertIn(location_def_wh1, crm_team2.location_ids)

    def test_check_update_locations_when_copy_location_01(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        location_def_wh1 = self.warehouse1.out_type_id.default_location_src_id
        self.assertIn(location_def_wh1, crm_team1.location_ids)
        location_def_wh2 = self.warehouse2.out_type_id.default_location_src_id
        crm_team2 = self.create_crm_team('2', self.warehouse2)
        new_location_wh2 = location_def_wh1.copy({
            'name': 'New location wh2',
            'location_id': location_def_wh2.id,
        })
        self.assertNotIn(new_location_wh2, crm_team1.location_ids)
        self.assertIn(new_location_wh2, crm_team2.location_ids)

    def test_check_unlink_locations_when_copy_location_01(self):
        crm_team1 = self.create_crm_team('1', self.warehouse1)
        location_def_wh1 = self.warehouse1.out_type_id.default_location_src_id
        self.assertIn(location_def_wh1, crm_team1.location_ids)
        new_location_wh1 = location_def_wh1.copy({
            'name': 'New location wh1',
        })
        self.assertIn(new_location_wh1, crm_team1.location_ids)
        new_location_wh1.unlink()
        self.assertNotIn(new_location_wh1, crm_team1.location_ids)
