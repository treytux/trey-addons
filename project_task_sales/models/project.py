# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    order_count = fields.Integer(
        string='Order count',
        compute='_compute_order_count')

    @api.one
    def _compute_order_count(self):
        self.order_count = self.env['sale.order'].search_count(
            [('project_id', '=', self.analytic_account_id.id)])

    @api.multi
    def sale_tree_view(self):
        return {
            'name': _('Sale Orders'),
            'domain': [('project_id', '=', self.analytic_account_id.id)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s', "
                       "'default_res_id': %d, "
                       "'search_default_partner_id': %d, "
                       "'default_project_id': %d}" % (
                self._name,
                self.analytic_account_id.id,
                self.partner_id.id,
                self.analytic_account_id.id)}
