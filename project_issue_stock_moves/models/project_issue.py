# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class ProjectIssue(models.Model):
    _inherit = 'project.issue'

    move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='issue_id',
        string='Stock Moves')
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='issue_id',
        string='Pickings')
    picking_count = fields.Integer(
        string='Picking count',
        compute='_compute_stock_count')
    move_count = fields.Integer(
        string='Moves count',
        compute='_compute_stock_count')

    @api.one
    @api.depends('picking_ids', 'move_ids')
    def _compute_stock_count(self):
        self.picking_count = len(self.picking_ids)
        self.move_count = len(self.move_ids)

    @api.multi
    def move_tree_view(self):
        return {
            'name': _('Stock Moves'),
            'domain': [('issue_id', '=', self.id)],
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.id)}

    @api.multi
    def picking_tree_view(self):
        return {
            'name': _('Pickings'),
            'domain': [('issue_id', '=', self.id)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.id)}
