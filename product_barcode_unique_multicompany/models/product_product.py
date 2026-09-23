###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [
        ('barcode_uniq', 'CHECK(1=1)', 'This constraint will never fail.')
    ]

    @api.constrains('barcode')
    def _check_barcode_unique(self):
        for product in self:
            if not product.barcode:
                continue
            product_count = self.env['product.product'].search_count([
                ('barcode', '=', product.barcode),
                ('id', '!=', product.id),
                '|',
                ('company_id', '=', False),
                ('company_id', '=', product.company_id.id),
            ])
            if product_count:
                raise ValidationError(_(
                    'The barcode %s already exists in another product for '
                    'this company. It must be unique!') % product.barcode)
