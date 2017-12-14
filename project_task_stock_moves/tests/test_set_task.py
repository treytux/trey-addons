# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestSetTask(common.TransactionCase):

    def setUp(self):
        super(TestSetTask, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_task_stock_moves',
            'is_company': True,
            'customer': True})
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_task_stock_moves'})
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_task_stock_moves',
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.project2 = self.env['project.project'].create({
            'name': 'Proyect second for test project_task_stock_moves',
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.task = self.env['project.task'].create({
            'name': 'Task for test project_task_stock_moves',
            'project_id': self.project.id})
        self.task2 = self.env['project.task'].create({
            'name': 'Task second for test project_task_stock_moves',
            'project_id': self.project.id})

    def test_picking(self):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing')])[0]
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'project_id': self.project.analytic_account_id.id,
            'task_id': self.task.id,
            'invoice_state': '2binvoiced',
            'picking_type_id': picking_type.id})
        self.assertEquals(
            picking.project_id, self.project.analytic_account_id)
        self.assertEquals(picking.task_id, self.task)

        location = self.env.ref('stock.stock_location_customers')
        move = self.env['stock.move'].create({
            'picking_id': picking.id,
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'location_id': location.id,
            'location_dest_id': location.id,
            'product_uom_qty': 1})
        self.assertEquals(move.project_id, picking.project_id)
        self.assertEquals(move.task_id, picking.task_id)

        # Test counters
        self.task = self.env['project.task'].browse(self.task.id)
        self.assertEquals(self.task.picking_count, 1)
        self.assertEquals(self.task.move_count, 1)
        self.assertEquals(self.project.picking_count, 1)
        self.assertEquals(self.project.move_count, 1)

        # Tests write picking
        picking.project_id = self.project2.analytic_account_id.id
        move = self.env['stock.move'].browse(move.id)
        self.assertEqual(picking.project_id, move.project_id)
        picking.task_id = self.task2.id
        move = self.env['stock.move'].browse(move.id)
        self.assertEqual(picking.task_id, move.task_id)

        # Tests write move, not set task_id to picking
        move.task_id = self.task.id
        picking = self.env['stock.picking'].browse(picking.id)
        self.assertNotEqual(move.task_id, picking.task_id)

        # Try create a picking with different partner of project
        partner2 = self.env['res.partner'].create({
            'name': 'Partner alternative for test project_task_stock_moves',
            'is_company': True,
            'customer': True})
        data = {
            'partner_id': partner2.id,
            'project_id': self.project.analytic_account_id.id,
            'task_id': self.task.id,
            'invoice_state': '2binvoiced',
            'picking_type_id': picking_type.id}
        try:
            self.env['stock.picking'].create(data)
        except Exception as e:
            _log.info('X' * 80)
            _log.info(('e', e))
            _log.info(('e', type(e)))
            _log.info('X' * 80)
        self.assertRaise(Exception, self.env['stock.picking'].create, (data))

        # Try write...
        data['partner_id'] = self.partner.id
        picking = self.env['stock.picking'].create(data)
        self.assertRaise(
            Exception,
            self.env['stock.picking'].write,
            (dict(partner_id=partner2.id)))
