# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    move_ids = fields.One2many(
        comodel_name='stock.move',
        inverse_name='task_id',
        string='Stock Moves')
    picking_ids = fields.One2many(
        comodel_name='stock.picking',
        inverse_name='task_id',
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
        context = {
            'default_res_model': self._name,
            'default_res_id': self.id,
        }
        return {
            'name': _('Stock Moves'),
            'domain': [('task_id', '=', self.id)],
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context.__str__()}

    @api.multi
    def picking_tree_view(self):
        context = {
            'default_res_model': self._name,
            'default_res_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_project_id': self.project_id.id,
            'default_task_id': self.id,
        }
        return {
            'name': _('Pickings'),
            'domain': [('task_id', '=', self.id)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context.__str__()}
