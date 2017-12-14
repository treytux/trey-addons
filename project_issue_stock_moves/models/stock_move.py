# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api
import logging
_log = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        string='Issue')

    @api.model
    def create(self, vals):
        vals = self._set_issue(vals)
        return super(StockMove, self).create(vals)

    @api.one
    def write(self, vals):
        vals = self._set_issue(vals)
        return super(StockMove, self).write(vals)

    @api.model
    def _set_issue(self, vals):
        if 'issue_id' in vals:
            return vals
        if 'picking_id' not in vals:
            return vals
        picking = self.env['stock.picking'].browse(vals['picking_id'])
        if picking.issue_id:
            vals['issue_id'] = picking.issue_id.id
        elif picking.sale_id:
            vals['issue_id'] = picking.sale_id.issue_id.id
        else:
            vals['issue_id'] = None
        return vals
