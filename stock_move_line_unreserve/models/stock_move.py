###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import api, models


class Picking(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def unreserve_stock_line(self):
        self.ensure_one()
        self._do_unreserve()
