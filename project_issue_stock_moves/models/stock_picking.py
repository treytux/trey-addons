# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        string='Issue')

    @api.model
    def create(self, vals):
        vals = self._set_issue(vals)
        result = super(StockPicking, self).create(vals)
        for record in result.move_lines:
            record.issue_id = result.issue_id.id
        return result

    @api.one
    def write(self, vals):
        vals = self.issue_id and vals or self._set_issue(vals)
        result = super(StockPicking, self).write(vals)
        for record in self.move_lines:
            record.issue_id = self.issue_id.id
        return result

    @api.model
    def _set_issue(self, vals):
        if 'issue_id' in vals:
            return vals
        if 'sale_id' not in vals:
            vals['issue_id'] = None
            return vals
        sale = self.env['sale.order'].browse(vals['sale_id'])
        vals['issue_id'] = sale.sale_id.issue_id.id
        return vals
