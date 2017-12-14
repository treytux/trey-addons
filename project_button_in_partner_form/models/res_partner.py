# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields, api, _
import logging
_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_totals = fields.Integer(
        string='Projects',
        readonly=True,
        compute='_get_project_totals')

    @api.one
    def _get_project_totals(self):
        if self.is_company:
            projects = self.env['project.project'].search_count(
                [('partner_id', '=', self.id)])
            self.project_totals = int(projects)

    @api.multi
    def project_tree_view(self):
        context = {
            'default_res_model': self._name,
            'default_res_id': self.id}
        return {
            'name': _('Projects'),
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context.__str__()}
