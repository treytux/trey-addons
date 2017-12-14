# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    task_ids = fields.Many2many(
        comodel_name='project.task',
        compute='_compute_task_ids')

    @api.one
    @api.depends('invoice_line')
    def _compute_task_ids(self):
        self.task_ids = list(set([l.task_id.id for l in self.invoice_line]))
