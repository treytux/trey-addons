###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo.tests.common import TransactionCase


class TestProjectBlockPicking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Blockable project',
        })
        self.task = self.env['project.task'].create({
            'name': 'Task 1',
            'project_id': self.project.id,
        })
        self.product = self.env['product.product'].create({
            'name': 'Product test',
            'type': 'product',
        })
        picking_type = self.env.ref('stock.picking_type_out')
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.env.ref(
                'stock.stock_location_customers').id,
            'task_id': self.task.id,
        })

    def test_not_blocked_by_default(self):
        self.assertFalse(self.picking.picking_blocked)

    def test_blocked_by_kanban_state(self):
        self.task.kanban_state = 'blocked'
        self.assertTrue(self.picking.picking_blocked)

    def test_blocked_by_project_flag(self):
        self.project.block_picking = True
        self.assertTrue(self.picking.picking_blocked)

    def test_blocked_by_archived_project(self):
        self.project.active = False
        self.assertTrue(self.picking.picking_blocked)

    def test_blocked_by_folded_stage(self):
        stage = self.env['project.project.stage'].create({
            'name': 'Closed',
            'fold': True,
        })
        self.project.stage_id = stage.id
        self.assertTrue(self.picking.picking_blocked)

    def test_unblock_restores_registration(self):
        self.task.kanban_state = 'blocked'
        self.task.kanban_state = 'normal'
        self.assertFalse(self.picking.picking_blocked)

    def test_picking_without_task_not_blocked(self):
        self.picking.task_id = False
        self.assertFalse(self.picking.picking_blocked)

    def test_compute_without_project_stages_group(self):
        group = self.env.ref('project.group_project_stages')
        user = self.env['res.users'].create({
            'name': 'Stock user',
            'login': 'stock_user_block',
            'groups_id': [
                (4, self.env.ref('stock.group_stock_user').id),
                (4, self.env.ref('project.group_project_user').id),
                (3, group.id),
            ],
        })
        picking = self.picking.with_user(user)
        self.assertFalse(picking.picking_blocked)
        self.project.block_picking = True
        self.assertTrue(picking.picking_blocked)
