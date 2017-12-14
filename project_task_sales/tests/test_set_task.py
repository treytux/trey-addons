# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestSetTask(common.TransactionCase):

    def setUp(self):
        super(TestSetTask, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_task_sales',
            'is_company': True,
            'customer': True})
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_task_sales',
            'type': 'product'})
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_task_sales',
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.project2 = self.env['project.project'].create({
            'name': 'Proyect second for test project_task_sales',
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.task = self.env['project.task'].create({
            'name': 'Task for test project_task_sales',
            'project_id': self.project.id})
        self.task2 = self.env['project.task'].create({
            'name': 'Task second for test project_task_sales',
            'project_id': self.project.id})

    def test_sale(self):
        wh = self.env['stock.warehouse'].search([])[0]
        order = self.env['sale.order'].create({
            'task_id': self.task.id,
            'warehouse_id': wh.id,
            'picking_policy': 'direct',
            'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1})
        order.action_button_confirm()
        picking = order.picking_ids[0]
        self.assertEqual(
            picking.project_id, order.task_id.project_id.analytic_account_id)
        self.assertEqual(picking.task_id, order.task_id)
        for move in picking.move_lines:
            self.assertEqual(
                move.project_id, order.task_id.project_id.analytic_account_id)
            self.assertEqual(move.task_id, order.task_id)

        # Test counters
        self.task = self.env['project.task'].browse(self.task.id)
        self.assertEquals(self.task.picking_count, 1)
        self.assertEquals(self.task.move_count, 1)
        self.project = self.env['project.project'].browse(self.project.id)
        self.assertEquals(self.project.picking_count, 1)
        self.assertEquals(self.project.move_count, 1)
