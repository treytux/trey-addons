###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    root_category = fields.Many2one(
        'product.public.category',
        compute='_compute_root_category',
        string='Root Category',
        store=True)

    @api.model
    def _get_root_category_recursive(self, category):
        if not category.parent_id:
            return category
        else:
            return self._get_root_category_recursive(category.parent_id)

    @api.one
    @api.depends('parent_id')
    def _compute_root_category(self):
        self.root_category = self._get_root_category_recursive(self)
