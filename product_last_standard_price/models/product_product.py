###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from datetime import datetime

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_standard_price_date = fields.Datetime(
        string='Last standard price date',
        compute='_compute_last_standard_price_date',
        store=True,
    )

    @api.depends('standard_price')
    def _compute_last_standard_price_date(self):
        price_history_obj = self.env['product.price.history']
        company_id = self.env.user.company_id.id
        for product in self:
            last_price_history = price_history_obj.search([
                ('company_id', '=', company_id),
                ('product_id', '=', product.id),
            ], order='create_date desc', limit=1)
            if not last_price_history:
                product.last_standard_price_date = datetime.now()
                continue
            product.last_standard_price_date = last_price_history.datetime
