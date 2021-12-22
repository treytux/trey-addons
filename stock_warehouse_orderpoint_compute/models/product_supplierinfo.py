###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.onchange('name')
    def onchange_name(self):
        if not self.name:
            return
        self.delay = self.name.supplierinfo_delay
