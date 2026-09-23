###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = 'product.category'

    code_seq = fields.Char(
        string='Code',
        size=2,
        help='This code is used for generate the default code for product.',
    )

    @api.constrains('code_seq')
    def _check_code_seq(self):
        categories = self.search([
            ('id', '!=', self.id),
            ('code_seq', '=', self.code_seq),
        ])
        if categories:
            raise ValidationError(_(
                'Error! Code already exists. The code must be unique.'))
