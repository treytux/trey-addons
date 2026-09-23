###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    project_ids = fields.One2many(
        comodel_name='project.project',
        inverse_name='partner_id',
        string='Projects',
    )
    project_count = fields.Integer(
        string='# Projects',
        compute='_compute_project_count',
    )

    def _compute_project_count(self):
        all_partners = self.with_context(active_test=False).search([
            ('id', 'child_of', self.ids),
        ])
        all_partners.read(['parent_id'])
        project_data = self.env['project.project']._read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'],
            groupby=['partner_id'],
        )
        self.project_count = 0
        for group in project_data:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.project_count += group['partner_id_count']
                partner = partner.parent_id

    def action_open_projects(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'project.open_view_project_all')
        action['domain'] = [('partner_id', 'child_of', self.id)]
        action['context'] = {
            'search_default_partner_id': self.id,
            'default_partner_id': self.id,
        }
        return action
