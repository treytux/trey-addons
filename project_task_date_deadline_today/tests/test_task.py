# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.tests import common
from openerp import fields


class TestTask(common.TransactionCase):

    def setUp(self):
        super(TestTask, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner for test project_task_sales',
            'is_company': True,
            'customer': True,
        })
        self.product = self.env['product.product'].create({
            'name': 'Product for test project_task_sales',
            'type': 'service',
        })
        self.project = self.env['project.project'].create({
            'name': 'Proyect for test project_task_sales',
            'use_tasks': True,
            'partner_id': self.partner.id,
        })

    def test_task_date_limit(self):
        task = self.env['project.task'].create({
            'name': 'Task for test project_task_sales',
            'project_id': self.project.id,
        })
        self.assertEquals(task.date_deadline, fields.Date.today())
        task = self.env['project.task'].create({
            'name': 'Task for test project_task_sales',
            'project_id': self.project.id,
        })
        self.assertEquals(task.date_deadline, fields.Date.today())
