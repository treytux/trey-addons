##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RentalForecast(models.Model):
    _name = 'rental.forecast'
    _description = 'Daily rental availability forecast'
    _order = 'date, product_id, warehouse_id'
    _rec_name = 'date'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        index=True,
        ondelete='cascade',
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        index=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        index=True,
    )
    date = fields.Date(
        string='Start date',
        required=True,
        index=True,
    )
    date_end = fields.Date(
        string='End date',
        index=True,
    )
    available_to_rent = fields.Float(
        string='Available to Rent',
        digits='Product unit of measure',
        group_operator='avg',
    )
    potential_demand = fields.Float(
        string='Potential Demand',
        digits='Product unit of measure',
    )
    _sql_constraints = [
        (
            'forecast_unique',
            'unique(product_id, warehouse_id, date)',
            'Forecast intervals must be unique.',
        ),
        (
            'forecast_dates',
            'check(date_end IS NULL OR date_end >= date)',
            'Forecast interval end must not precede its start.',
        ),
    ]

    @api.model
    def _get_forecast_period(self):
        parameter = self.env['ir.config_parameter'].sudo().get_param(
            'stock.report_stock_quantity_period', default='3')
        try:
            months = max(1, int(parameter))
        except (TypeError, ValueError):
            months = 3
        today = fields.Date.today()
        return (
            today - relativedelta(months=months),
            today + relativedelta(months=months))

    @api.model
    def generate(self, product, warehouse, start_date=None, days=365):
        start_date = fields.Date.to_date(start_date or fields.Date.today())
        end_date = start_date + timedelta(days=days - 1)
        product = product.with_company(warehouse.company_id)
        self.search([
            ('product_id', '=', product.id),
            ('warehouse_id', '=', warehouse.id),
        ]).unlink()
        service = self.env['rental.availability']
        projection = service._get_projection_data(
            product, warehouse, start_date, end_date)
        boundaries = {start_date, end_date + timedelta(days=1)}
        boundaries.update(
            day for day in projection['events']
            if start_date <= day <= end_date)
        boundaries.update(
            day for day in projection['potential_events']
            if start_date <= day <= end_date)
        boundaries = sorted(boundaries)
        available = projection['available']
        potential = 0
        values = []
        for index, interval_start in enumerate(boundaries[:-1]):
            available += projection['events'].get(interval_start, 0)
            potential += projection['potential_events'].get(interval_start, 0)
            interval_end = boundaries[index + 1] - timedelta(days=1)
            if interval_start > interval_end:
                continue
            values.append({
                'product_id': product.id,
                'warehouse_id': warehouse.id,
                'company_id': warehouse.company_id.id,
                'date': interval_start,
                'date_end': min(interval_end, end_date),
                'available_to_rent': available,
                'potential_demand': potential,
            })
        return self.create(values)

    @api.model
    def generate_for_product_warehouse(self, product_id, warehouse_id):
        product = self.env['product.product'].browse(product_id).exists()
        warehouse = self.env['stock.warehouse'].browse(warehouse_id).exists()
        if not product or not warehouse:
            raise UserError(_('The product or warehouse no longer exists.'))
        if warehouse.company_id != self.env.company:
            raise UserError(_('Select a warehouse in the current company.'))
        if not warehouse.rental_in_location_id:
            raise UserError(_(
                'The selected warehouse is not enabled for rentals.'))
        start_date, end_date = self._get_forecast_period()
        return self.generate(
            product.with_company(warehouse.company_id), warehouse,
            start_date=start_date, days=(end_date - start_date).days + 1).ids

    @api.model
    def action_open_for_product(self, product):
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id),
            ('rental_in_location_id', '!=', False),
        ], limit=1)
        if not warehouse:
            return False
        start_date, end_date = self._get_forecast_period()
        self.generate(
            product, warehouse, start_date=start_date,
            days=(end_date - start_date).days + 1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rental Forecast',
            'res_model': 'rental.forecast.daily',
            'view_mode': 'graph,tree',
            'views': [
                (self.env.ref(
                    'rental_availability_forecast.rental_forecast_graph').id,
                    'graph'),
                (self.env.ref('rental_availability_forecast.'
                              'rental_forecast_daily_tree').id, 'tree'), ],
            'domain': [
                ('product_id', '=', product.id),
                ('warehouse_id', '=', warehouse.id), ],
            'context': {'search_default_product_id': product.id}, }
