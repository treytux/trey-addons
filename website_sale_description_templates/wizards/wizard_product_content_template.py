###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class WizardProductContentTemplate(models.TransientModel):
    _name = 'wizard.product.content.template'
    _description = 'Wizard to set product content template'

    content_template = fields.Many2one(
        comodel_name='product.content.template',
        string='Content template',
    )

    def button_set_content_template(self):
        product = self.env[self.env.context.get('active_model')].browse(
            self.env.context.get('active_id', []))
        render = self.env['mail.template']._render_template(
            self.content_template.body_html,
            self.env.context.get('active_model'), product.id)
        product.website_description = render
