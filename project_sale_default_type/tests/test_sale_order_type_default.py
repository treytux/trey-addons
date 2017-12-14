# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common


class TestSaleOrderType(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrderType, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_sale_default_type',
            'issue_warn': 'no-message',
            'task_warn': 'no-message',
            'is_company': True,
            'customer': True})
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_sale_default_type',
            'type': 'product'})
        wh = self.env['stock.warehouse'].search([], limit=1)
        self.order_type = self.env['sale.order.type'].create({
            'name': 'Order Type for test project_sale_default_type',
            'warehouse_id': wh[0].id})
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_sale_default_type',
            'sale_order_type_id': self.order_type.id,
            'use_tasks': True,
            'partner_id': self.partner.id})
        self.task = self.env['project.task'].create({
            'name': 'Task for test project_sale_default_type',
            'project_id': self.project.id})

    def test_sale(self):
        wh = self.env['stock.warehouse'].search([])[0]
        order = self.env['sale.order'].create({
            'project_id': self.project.analytic_account_id.id,
            'warehouse_id': wh.id,
            'picking_policy': 'direct',
            'partner_id': self.partner.id})
        order.onchange_project_id()
        self.assertEqual(order.type_id.id, self.order_type.id)
