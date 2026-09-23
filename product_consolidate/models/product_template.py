###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_consolidated = fields.Boolean(
        string='Is Consolidated',
        copy=False,
    )

    def toogle_consolidate_products(self):
        for template in self:
            template.is_consolidated = not template.is_consolidated
        return True
