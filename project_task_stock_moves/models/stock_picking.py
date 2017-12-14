# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, exceptions, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    project_id = fields.Many2one(
        comodel_name='account.analytic.account',
        domain="[('partner_id', '=', partner_id)]",
        string='Project')
    task_id = fields.Many2one(
        comodel_name='project.task',
        string='Task')

    @api.model
    def create(self, vals):
        vals = self._set_project_and_task(vals)
        result = super(StockPicking, self).create(vals)
        project = result.project_id
        if project and project.partner_id != result.partner_id:
            raise exceptions.Warning(
                _('If you set a project the partner of picking '
                  'must is the same that project partner.'))
        for record in result.move_lines:
            record.write({
                'project_id': result.project_id.id,
                'task_id': result.task_id.id})
        return result

    @api.one
    def write(self, vals):
        vals = self._set_project_and_task(vals)
        result = super(StockPicking, self).write(vals)
        for record in self.move_lines:
            record.write({
                'project_id': self.project_id.id,
                'task_id': self.task_id.id})
        return result

    @api.model
    def _set_project_and_task(self, vals):
        if 'picking_id' not in vals:
            return vals
        picking = self.env['stock.picking'].browse(vals['picking_id'])
        vals['project_id'] = (
            picking.project_id and picking.project_id.id or None)
        vals['task_id'] = (picking.task_id and picking.task_id.id or None)
        return vals
