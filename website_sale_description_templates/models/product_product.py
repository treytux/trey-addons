###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_set_content_template(self):
        self.ensure_one()
        action = self.env.ref(
            'website_sale_description_templates.content_template_wzd_action')
        action = action.read()[0]
        return action
