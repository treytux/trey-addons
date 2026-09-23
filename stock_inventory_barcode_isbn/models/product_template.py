###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    authors = fields.Char(
        string='Authors',
    )
    categories = fields.Char(
        string='Categories',
    )
    description = fields.Char(
        string='Description',
    )
    language = fields.Char(
        string='Language',
    )
    page_count = fields.Char(
        string='Page count',
    )
    published_date = fields.Char(
        string='Published date',
    )
    publishers = fields.Char(
        string='Publishers',
    )
