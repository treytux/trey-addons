###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductContentTemplate(models.Model):
    _name = 'product.content.template'
    _description = 'Product content template'

    name = fields.Char(
        string='Name',
    )
    body_html = fields.Html(
        string='Content',
        translate=True,
        sanitize=False,
    )
