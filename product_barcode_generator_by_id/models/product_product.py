###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_assign_barcode(self):
        for record in self:
            barcode = self._get_barcode_next_code(record)
            record.barcode = barcode

    def _get_barcode_next_code(self, product):
        category_prefix = product.categ_id.barcode_sequence_id.prefix or ''
        company_prefix = product.company_id.barcode_sequence_id.prefix or ''
        prefix = f'{category_prefix}{company_prefix}'
        return f'{prefix}{(product.id or 0):012d}'
