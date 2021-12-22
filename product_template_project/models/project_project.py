###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product template',
    )
