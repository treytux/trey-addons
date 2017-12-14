# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    project_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Project')
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task')

    @api.model
    def create(self, vals):
        vals = self._set_project_and_task(vals)
        return super(StockMove, self).create(vals)

    @api.one
    def write(self, vals):
        vals = self._set_project_and_task(vals)
        return super(StockMove, self).write(vals)

    @api.model
    def _set_project_and_task(self, vals):
        if 'picking_id' not in vals:
            return vals
        picking = self.env['stock.picking'].browse(vals['picking_id'])
        if picking.project_id:
            vals['project_id'] = picking.project_id.id
        elif picking.sale_id:
            vals['project_id'] = picking.sale_id.project_id.id
        if picking.task_id:
            vals['task_id'] = picking.task_id.id
        elif picking.sale_id:
            vals['task_id'] = picking.sale_id.task_id.id
        return vals
