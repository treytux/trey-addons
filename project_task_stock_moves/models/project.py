# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    picking_count = fields.Integer(
        string='Picking count',
        compute='_compute_stock_count')
    move_count = fields.Integer(
        string='Moves count',
        compute='_compute_stock_count')

    @api.one
    def _compute_stock_count(self):
        self.move_count = self.env['stock.move'].search_count(
            [('project_id', '=', self.analytic_account_id.id)])
        self.picking_count = self.env['stock.picking'].search_count(
            [('project_id', '=', self.analytic_account_id.id)])

    @api.multi
    def move_tree_view(self):
        return {
            'name': _('Stock Moves'),
            'domain': [('project_id', '=', self.analytic_account_id.id)],
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.analytic_account_id.id)}

    @api.multi
    def picking_tree_view(self):
        return {
            'name': _('Pickings'),
            'domain': [('project_id', '=', self.analytic_account_id.id)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.analytic_account_id.id)}
