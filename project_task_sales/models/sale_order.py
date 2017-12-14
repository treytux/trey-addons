# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task_id = fields.Many2one(
        comodel_name='project.task',
        domain="[('project_id.analytic_account_id', '=', project_id)]",
        string='Task')

    @api.onchange('task_id')
    def onchange_task_id(self):
        if self.task_id:
            ac = (self.task_id.project_id and
                  self.task_id.project_id.analytic_account_id or None)
            self.project_id = ac and ac.id or None
            self.partner_id = ac and ac.partner_id and ac.partner_id.id or None

    @api.one
    def action_button_confirm(self):
        res = super(SaleOrder, self).action_button_confirm()
        project_id = (
            (self.task_id and self.task_id.project_id and
             self.task_id.project_id.analytic_account_id) and
            self.task_id.project_id.analytic_account_id.id or None)
        for picking in self.picking_ids:
            picking.write({
                'project_id': project_id,
                'task_id': self.task_id.id})
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task')

    @api.model
    def create(self, vals):
        order = self.env['sale.order'].browse(vals['order_id'])
        vals['task_id'] = order.task_id.id
        return super(SaleOrderLine, self).create(vals)
