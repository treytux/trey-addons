# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        domain="[('project_id.analytic_account_id', '=', project_id)]",
        string='Issue')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    issue_id = fields.Many2one(
        comodel_name='project.issue',
        string='Issue')
    issue_line_id = fields.Many2one(
        comodel_name='project.issue.line',
        string='Issue Line')

    @api.model
    def create(self, vals):
        order = self.env['sale.order'].browse(vals['order_id'])
        vals['issue_id'] = order.issue_id.id
        return super(SaleOrderLine, self).create(vals)
