###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, values):
        if (not self.env.user.has_group(
                'product_creation_acl.group_product_creation')
                and not self.env.context.get('install_mode', False)):
            raise ValidationError(_('You are not allowed to create products.'))
        return super().create(values)
