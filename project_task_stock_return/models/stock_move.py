# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task')
    project_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Project')

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        res.set_project_and_task()
        return res

    @api.one
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        self.set_project_and_task()
        return res

    @api.multi
    def set_project_and_task(self):
        sale_id = self.picking_id and self.picking_id.sale_id or None
        if not sale_id:
            return False
        if not self.task_id and sale_id.task_id:
            self.task_id = sale_id.task_id.id
        if not self.project_id and sale_id.project_id:
            self.project_id = sale_id.project_id.id
        if not self.picking_id.task_id and sale_id.task_id:
            self.picking_id.task_id = sale_id.task_id.id
        if not self.picking_id.project_id and sale_id.project_id:
            self.picking_id.project_id = sale_id.project_id.id
