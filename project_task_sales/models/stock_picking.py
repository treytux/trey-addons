# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _set_project_and_task(self, vals):
        vals = super(StockPicking, self)._set_project_and_task(vals)
        if 'picking_id' not in vals:
            return vals
        picking = self.env['stock.picking'].browse(vals['picking_id'])
        if not picking.sale_id:
            return vals
        if not vals.get('project_id', None):
            vals['project_id'] = picking.sale_id.task_id.project_id.id
        if not vals.get('task_id', None):
            vals['task_id'] = picking.sale_id.task_id.id
        return vals
