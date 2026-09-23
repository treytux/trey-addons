##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import fields, models, tools


class RentalForecastDaily(models.Model):
    _name = 'rental.forecast.daily'
    _description = 'Daily rental forecast (Reporting view)'
    _auto = False
    _order = 'date, product_id, warehouse_id'
    _rec_name = 'date'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        readonly=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    date = fields.Date(
        string='Date',
        readonly=True,
    )
    available_to_rent = fields.Float(
        string='Available to Rent',
        digits='Product unit of measure',
        readonly=True,
        group_operator='avg',
    )
    potential_demand = fields.Float(
        string='Potential Demand',
        digits='Product Unit of measure',
        readonly=True,
        group_operator='avg',
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            '''
            CREATE VIEW rental_forecast_daily AS (
                SELECT
                    row_number() OVER (
                        ORDER BY f.product_id, f.warehouse_id, dates.day
                    ) AS id,
                    f.product_id,
                    f.warehouse_id,
                    f.company_id,
                    dates.day::date AS date,
                    f.available_to_rent,
                    f.potential_demand
                FROM rental_forecast f
                CROSS JOIN LATERAL generate_series(
                    f.date,
                    COALESCE(f.date_end, f.date),
                    interval '1 day'
                ) AS dates(day)
            )
            ''')
