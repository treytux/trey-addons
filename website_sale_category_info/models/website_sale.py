###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models
from odoo.tools.translate import html_translate


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    website_description = fields.Html(
        string='Website description',
        sanitize_attributes=False,
        translate=html_translate)
