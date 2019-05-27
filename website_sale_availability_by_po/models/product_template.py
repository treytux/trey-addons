###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    stock_state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('latest_units', 'Latest Units'),
            ('coming_soon', 'Coming Soon'),
            ('not_available', 'Not Available')],
        string='Stock State',
        compute='_compute_stock_state')

    @api.one
    @api.depends('product_variant_ids')
    def _compute_stock_state(self):
        states = [v.stock_state for v in self.product_variant_ids]
        if all([s == 'available' for s in states]):
            self.stock_state = 'available'
        elif any([s == 'latest_units' for s in states]):
            self.stock_state = 'latest_units'
        elif any([s == 'coming_soon' for s in states]):
            self.stock_state = 'coming_soon'
        elif all([s == 'not_available' for s in states]):
            self.stock_state = 'not_available'
