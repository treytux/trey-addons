###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    content_template = fields.Many2one(
        string='Content template',
        comodel_name='product.content.template',
    )

    def action_set_content_template(self):
        self.ensure_one()
        action = self.env.ref(
            'website_sale_description_templates.content_template_wzd_action')
        action = action.read()[0]
        return action
