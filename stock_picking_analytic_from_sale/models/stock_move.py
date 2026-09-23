###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_data_for_create_analytic_line(self):
        self.ensure_one()
        vals = super()._prepare_data_for_create_analytic_line()
        if not vals:
            return vals
        if self.sale_line_id and vals.get('name'):
            vals['name'] = '{} - {}'.format(
                self.sale_line_id.order_id.name, vals['name'])
        return vals
