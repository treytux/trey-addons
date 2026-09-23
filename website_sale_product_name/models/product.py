###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    public_name = fields.Char(
        string='Public name',
        translate=True,
    )
    website_name = fields.Char(
        string='Website name',
        compute='_compute_website_name',
        translate=True,
    )

    @api.depends('public_name', 'name')
    def _compute_website_name(self):
        for product in self:
            if product.public_name:
                product.website_name = product.public_name
            else:
                product.website_name = product.name
