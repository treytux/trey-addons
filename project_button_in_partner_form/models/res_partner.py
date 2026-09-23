###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging

from odoo import _, api, fields, models

_log = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_totals = fields.Integer(
        string='Projects',
        readonly=True,
        compute='_compute_project_totals',
    )

    @api.depends('is_company')
    def _compute_project_totals(self):
        for partner in self:
            if partner.is_company:
                project_count = self.env['project.project'].search_count([
                    ('partner_id', '=', partner.id),
                ])
                partner.project_totals = project_count
            else:
                partner.project_totals = 0

    def action_view_projects(self):
        self.ensure_one()
        return {
            'name': _('Projects'),
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'view_id': False,
            'limit': 80,
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }
