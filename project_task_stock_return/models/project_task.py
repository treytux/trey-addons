# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.one
    def action_stock_return(self):
        return {
            'name': _('Pickings'),
            'domain': [('task_id', '=', self.id)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (
                self._name, self.id)}
