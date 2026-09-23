###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def unreserve_stock_line(self):
        self.ensure_one()
        self._do_unreserve()
