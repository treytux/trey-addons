###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    condition = fields.Selection(
        selection=[
            ('new', 'New'),
            ('used', 'Used'),
            ('refurb', 'Refurbished'),
            ('damaged', 'Damaged'),
        ],
        string='Condition',
        default='new',
    )
