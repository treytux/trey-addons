###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()
        if self.sale_line_id.supplierinfo_id:
            values['supplierinfo_id'] = self.sale_line_id.supplierinfo_id
        return values
