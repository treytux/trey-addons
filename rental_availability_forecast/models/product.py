##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    has_rented_product = fields.Boolean(
        compute='_compute_rental_visibility_helpers',
    )

    @api.depends('rented_product_id')
    def _compute_rental_visibility_helpers(self):
        for product in self:
            product.has_rented_product = bool(product.rented_product_id)

    def action_rental_forecast(self):
        self.ensure_one()
        rented_product = self.rented_product_id
        if not rented_product:
            return False
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
            ('rental_in_location_id', '!=', False),
        ], limit=1)
        if not warehouse:
            return False
        return {
            'type': 'ir.actions.client',
            'tag': 'rental_replenish_report',
            'name': 'Rental Forecast',
            'context': {
                'active_model': 'product.product',
                'active_id': rented_product.id,
                'warehouse': warehouse.id,
            },
        }

    def action_rental_forecast_events(self):
        self.ensure_one()
        rented_product = self.rented_product_id
        if not rented_product:
            return False
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
            ('rental_in_location_id', '!=', False),
        ], limit=1)
        if not warehouse:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Forecast Events',
            'res_model': 'rental.forecast.event',
            'view_mode': 'tree',
            'domain': [
                ('product_id', '=', rented_product.id),
                ('warehouse_id', '=', warehouse.id),
            ],
            'context': {'search_default_product_id': rented_product.id},
        }
