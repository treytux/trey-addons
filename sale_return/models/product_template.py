###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_returnable = fields.Boolean(
        default=True,
        string='Is returnable')
    product_returnable_days = fields.Integer(
        string='Product returnable days')
    returnable_days = fields.Integer(
        string='Returnable days',
        compute='_compute_returnable_days')

    @api.multi
    @api.depends('product_returnable_days')
    def _compute_returnable_days(self):
        for product in self:
            default_return_days = product.company_id.default_return_days
            days = product.product_returnable_days
            product.returnable_days = days and days or default_return_days
