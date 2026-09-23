###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_availability_dates(self):
        self.ensure_one()
        dates = super()._get_availability_dates()
        dates += self._get_mrp_availability_dates()
        return dates

    def _get_mrp_availability_dates(self):
        self.ensure_one()
        productions = self.env['mrp.production'].search_read([
            ('state', 'in', ['confirmed', 'progress']),
            ('product_id', '=', self.id),
            ('date_planned_start', '!=', False),
        ], ['date_planned_start'], order='date_planned_start asc')
        return [production['date_planned_start'] for production in productions]
