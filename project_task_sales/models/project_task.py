# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='task_id',
        string='Sale Orders')
    order_count = fields.Integer(
        string='Order count',
        compute='_compute_order_count')

    @api.one
    @api.depends('order_ids')
    def _compute_order_count(self):
        self.order_count = len(self.order_ids)

    @api.multi
    def sale_tree_view(self):
        return {
            'name': _('Sale Orders'),
            'domain': [('task_id', '=', self.id)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s', "
                       "'default_res_id': %d, "
                       "'search_default_partner_id': %d, "
                       "'default_task_id': %d, "
                       "'default_project_id': %d}" % (
                self._name,
                self.id,
                self.project_id.partner_id.id,
                self.id, self.project_id.analytic_account_id.id)}
