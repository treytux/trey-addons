# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
import logging
_log = logging.getLogger(__name__)


class TestInvoice(common.TransactionCase):

    def setUp(self):
        super(TestInvoice, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_task_invoice',
            'is_company': True,
            'customer': True})
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_task_invoice',
            'type': 'product'})
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_task_invoice',
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.task = self.env['project.task'].create({
            'name': 'Task for test project_task_invoice',
            'project_id': self.project.id})
        self.task2 = self.env['project.task'].create({
            'name': 'Task second for test project_task_invoice',
            'project_id': self.project.id})

    def test_sale(self):
        account = self.env['account.account'].search([], limit=1)[0]
        invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': account.id})
        self.env['account.invoice.line'].create({
            'task_id': self.task.id,
            'invoice_id': invoice.id,
            'product_id': self.product.id,
            'name': self.product.name,
            'account_id': account.id,
            'quantity': 1})
        self.assertTrue(self.task.id in invoice.task_ids.ids)

        # Test counters
        self.task = self.env['project.task'].browse(self.task.id)
        self.task2 = self.env['project.task'].browse(self.task2.id)
        self.assertEquals(self.task.invoice_count, 1)
        self.assertEquals(self.task2.invoice_count, 0)

        self.env['account.invoice.line'].create({
            'task_id': self.task2.id,
            'invoice_id': invoice.id,
            'product_id': self.product.id,
            'name': self.product.name,
            'account_id': account.id,
            'quantity': 1})
        self.task = self.env['project.task'].browse(self.task.id)
        self.task2 = self.env['project.task'].browse(self.task2.id)
        self.assertEquals(self.task.invoice_count, 1)
        self.assertEquals(self.task2.invoice_count, 1)
        self.assertTrue(self.task.id in invoice.task_ids.ids)
        self.assertTrue(self.task2.id in invoice.task_ids.ids)

    def test_create_invoice_from_task(self):
        self.project.pricelist_id = self.env.ref('product.list0')
        work = self.env['project.task.work'].create({
            'task_id': self.task.id,
            'hours': 1.0,
            'name': 'Task Work for test',
            'user_id': self.env.user.id})
        ctx = {
            'active_ids': [self.task.id],
            'default_res_model': 'project.task',
            'default_res_id': self.task.id}
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale')])[0]
        wiz = self.env['project.task.create_invoice'].with_context(
            ctx).create({
                'user_id': self.env.user.id,
                'project_id': self.project.id,
                'partner_id': self.partner.id,
                'journal_id': journal.id})
        wiz.with_context(ctx).onchange_user_id()
        self.assertIn(work.id, [w.work_id.id for w in wiz.work_ids])
        self.assertIn(self.task.id, [w.task_id.id for w in wiz.work_ids])

        re = wiz.with_context(ctx).button_accept()
        self.assertTrue('domain' in re)
        invoice = self.env['account.invoice'].search(re['domain'])[0]
        self.assertIn(self.task.id, invoice.task_ids.ids)

        self.task = self.env['project.task'].browse(self.task.id)
        self.assertEqual(self.task.invoice_count, 1)

        work = self.env['project.task.work'].browse(work.id)
        self.assertTrue(work.hr_analytic_timesheet_id.invoice_id)

        # No duplicate invoice for work invoiced
        wiz = self.env['project.task.create_invoice'].with_context(
            ctx).create({
                'user_id': self.env.user.id,
                'project_id': self.project.id,
                'partner_id': self.partner.id,
                'journal_id': journal.id})
        wiz.with_context(ctx).onchange_user_id()
        self.assertNotIn(work.id, [w.work_id for w in wiz.work_ids])

    def test_create_invoice_from_picking(self):
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing')])[0]
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'project_id': self.project.analytic_account_id.id,
            'task_id': self.task.id,
            'invoice_state': '2binvoiced',
            'picking_type_id': picking_type.id})
        location = self.env.ref('stock.stock_location_customers')
        move = self.env['stock.move'].create({
            'picking_id': picking.id,
            'name': self.product.name,
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'location_id': location.id,
            'location_dest_id': location.id,
            'product_uom_qty': 1})
        self.assertEquals(move.project_id.id, picking.project_id.id)
        self.assertEquals(move.task_id.id, picking.task_id.id)
        picking.invoice_state = '2binvoiced'  # The stock rule empty this field
        self.assertEquals(picking.invoice_state, '2binvoiced')

        picking.action_confirm()
        picking.action_assign()
        picking.do_transfer()

        self.assertEqual(self.task.picking_count, 1)
        self.assertEqual(self.task.move_count, 1)

        self.project.pricelist_id = self.env.ref('product.list0')
        work = self.env['project.task.work'].create({
            'task_id': self.task.id,
            'hours': 1.0,
            'name': 'Task Work for test',
            'user_id': self.env.user.id})
        ctx = {
            'active_ids': [self.task.id],
            'default_res_model': 'project.task',
            'default_res_id': self.task.id}
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale')])[0]
        wiz = self.env['project.task.create_invoice'].with_context(
            ctx).create({
                'user_id': self.env.user.id,
                'project_id': self.project.id,
                'partner_id': self.partner.id,
                'journal_id': journal.id})
        wiz.with_context(ctx).onchange_user_id()
        self.assertIn(work.id, [w.work_id.id for w in wiz.work_ids])
        self.assertIn(picking.id, [p.picking_id.id for p in wiz.picking_ids])

        re = wiz.with_context(ctx).button_accept()
        self.assertTrue('domain' in re)
        invoice = self.env['account.invoice'].search(re['domain'])[0]
        self.assertIn(self.task.id, invoice.task_ids.ids)
        for line in invoice.invoice_line:
            self.assertEqual(self.task, line.task_id)
