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

    @api.onchange('stock')
    def onchange_stock(self):
        self.date_stock = fields.Date.today()
