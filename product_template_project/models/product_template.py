###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    project_ids = fields.One2many(
        comodel_name='project.project',
        inverse_name='product_tmpl_id',
        string='Projects',
    )
    projects_count = fields.Integer(
        string='Projects count',
        compute='_compute_projects_count',
    )

    @api.depends('project_ids')
    def _compute_projects_count(self):
        for product in self:
            product.projects_count = len(product.project_ids)

    def action_view_projects(self):
        self.ensure_one()
        action = self.env.ref(
            'product_template_project.act_product_project_view').read()[0]
        if len(self.project_ids) > 0:
            action['domain'] = [('id', 'in', self.project_ids.ids)]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
