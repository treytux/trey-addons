###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def barcode_set(self):
        prefix = '84999'
        for product in self:
            code = '%s%s' % (prefix, str(product.id).zfill(12 - len(prefix)))
            dc = sum([(i % 2 and 3 or 1) * int(code[i]) for i in range(12)])
            dc = (10 - dc % 10) % 10
            product.barcode = '%s%s' % (code[:12], dc)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not res.barcode:
            res.barcode_set()
        return res

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        self.filtered(lambda p: not p.barcode).barcode_set()
        return res
