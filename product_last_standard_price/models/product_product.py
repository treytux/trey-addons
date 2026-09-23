###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    last_standard_price_date = fields.Datetime(
        string='Last standard price date',
        compute='_compute_last_standard_price_date',
        compute_sudo=True,
        store=True,
    )

    @api.depends('standard_price')
    def _compute_last_standard_price_date(self):
        valuation_layer_obj = self.env['stock.valuation.layer']
        company_id = self.env.company.id
        for product in self:
            last_valuation_layer = valuation_layer_obj.search([
                ('company_id', '=', company_id),
                ('product_id', '=', product.id),
            ], order='create_date desc, id desc', limit=1)
            product.last_standard_price_date = (
                last_valuation_layer.create_date
                or product.create_date
                or fields.Datetime.now()
            )
