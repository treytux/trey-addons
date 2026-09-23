###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    stock = fields.Float(
        string='Stock',
    )
    date_stock = fields.Date(
        string='Stock Date',
        readonly=True,
    )

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if 'stock' in vals:
            res.date_stock = fields.Date.today()
        return res

    def write(self, vals):
        res = super().write(vals)
        if 'stock' in vals:
            self.date_stock = fields.Date.today()
        return res
