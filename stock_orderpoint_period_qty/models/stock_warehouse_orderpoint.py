###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import float_round


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    product_min_qty_period = fields.Float(
        string='Last Period Demand',
        compute='_compute_historical_quantities',
        digits='Product Unit of Measure',
    )
    product_min_qty_month = fields.Float(
        string='Last Month Demand',
        compute='_compute_historical_quantities',
        digits='Product Unit of Measure',
    )

    def _get_period_values(self):
        self.ensure_one()
        values = {
            'annual': (relativedelta(years=1), 12),
            'semester': (relativedelta(months=6), 6),
            'quarterly': (relativedelta(months=3), 3),
            'monthly': (relativedelta(months=1), 1),
        }
        return values.get(
            self.company_id.period_min_qty, values['monthly'])

    def _get_historical_monthly_demand(self):
        self.ensure_one()
        period_delta, months = self._get_period_values()
        date_to = fields.Date.today()
        date_from = date_to - period_delta
        return self._get_historical_demand(date_from, date_to, months)

    def _get_historical_demand(self, date_from, date_to, months=1):
        self.ensure_one()
        in_moves = self._search_period_moves(
            date_from=date_from,
            date_to=date_to,
            location_dest_id=self.location_id.id)
        out_moves = self._search_period_moves(
            date_from=date_from,
            date_to=date_to,
            location_id=self.location_id.id)
        return round((
            sum(move['product_uom_qty'] for move in out_moves)
            - sum(move['product_uom_qty'] for move in in_moves)) / months, 0)

    @api.depends(
        'product_id', 'location_id', 'warehouse_id', 'company_id',
        'company_id.period_min_qty', 'product_id.stock_move_ids',
        'product_id.stock_move_ids.state', 'product_id.stock_move_ids.date',
        'product_id.stock_move_ids.product_uom_qty')
    def _compute_historical_quantities(self):
        date_to = fields.Date.today()
        for orderpoint in self:
            period_delta, months = orderpoint._get_period_values()
            orderpoint.product_min_qty_period = (
                orderpoint._get_historical_demand(
                    date_to - period_delta, date_to, months))
            orderpoint.product_min_qty_month = (
                orderpoint._get_historical_demand(
                    date_to - relativedelta(months=1), date_to))

    def _search_period_moves(
            self, date_from, date_to, location_id=None, location_dest_id=None):
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date', '<=', date_to),
            ('date', '>=', date_from),
            ('state', '!=', 'cancel'),
            ('product_id', '=', self.product_id.id),
        ]
        warehouse = self.warehouse_id
        if location_id:
            if warehouse.deposit_parent_id:
                domain.extend([
                    '|',
                    ('location_dest_id', 'in',
                     warehouse.deposit_parent_id.child_ids.ids),
                ])
            else:
                domain.append(('location_id', '=', location_id))
        else:
            if warehouse.deposit_parent_id:
                domain.extend([
                    ('location_dest_id', '=', location_dest_id),
                    '|',
                ])
            domain.append(
                ('location_id.usage', 'in', ['customer', 'production']))
        if location_dest_id:
            if warehouse.deposit_parent_id:
                domain.append((
                    'location_id', 'in',
                    warehouse.deposit_parent_id.child_ids.ids))
            else:
                domain.append(('location_dest_id', '=', location_dest_id))
        else:
            domain.append(
                ('location_dest_id.usage', 'in', ['customer', 'production']))
            if warehouse.deposit_parent_id:
                domain.append(('location_id', '=', location_id))
        return self.env['stock.move'].search_read(domain, ['product_uom_qty'])

    @api.depends(
        'qty_forecast', 'qty_multiple', 'product_id', 'location_id',
        'warehouse_id', 'company_id', 'company_id.period_min_qty',
        'product_id.stock_move_ids', 'product_id.stock_move_ids.state',
        'product_id.stock_move_ids.date',
        'product_id.stock_move_ids.product_uom_qty')
    def _compute_qty_to_order(self):
        super()._compute_qty_to_order()
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint.qty_to_order = False
                continue
            demand = orderpoint._get_historical_monthly_demand()
            qty_to_order = max(demand - orderpoint.qty_forecast, 0.0)
            if orderpoint.qty_multiple:
                qty_to_order = float_round(
                    qty_to_order, precision_rounding=orderpoint.qty_multiple,
                    rounding_method='UP')
            orderpoint.qty_to_order = qty_to_order
