###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from math import ceil

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockWarehouseOrderpoint(models.Model):
    _name = 'stock.warehouse.orderpoint'
    _inherit = [
        'stock.warehouse.orderpoint', 'mail.thread', 'mail.activity.mixin']

    product_min_qty = fields.Float(
        track_visibility='onchange',
    )
    product_max_qty = fields.Float(
        track_visibility='onchange',
    )

    def _get_sale_moves(self, product, date_init, date_end, delay):
        return sum(self.env['product.product.stock.rotation'].search([
            ('product_id', '=', product.id),
            ('date_day', '>=', date_init),
            ('date_day', '<=', date_end),
            ('qty_sale', '!=', 0.00),
        ], order='date_day asc').mapped('qty_sale'))

    def _get_purchase_move(self, product, date_init, date_end, delay):
        return self.env['product.product.stock.rotation'].search([
            ('product_id', '=', product.id),
            ('date_day', '>=', date_init),
            ('date_day', '<=', date_end),
            ('qty_purchase', '!=', 0.00),
        ], order='date_day desc', limit=1)

    def _compute_qtys(
            self, date_init, date_end, delay, factor_min, factor_max):
        if self.product_id.qty_available <= 0:
            purchase_move = self._get_purchase_move(
                self.product_id, date_init, date_end, delay)
            if purchase_move:
                date_without_stock = purchase_move.date_day
                date_init = date_without_stock
                qty_out = self._get_sale_moves(
                    self.product_id, date_without_stock, date_end, delay)
            else:
                delay = 1
                qty_out = self._get_sale_moves(
                    self.product_id, date_init, date_end, delay)
        else:
            qty_out = self._get_sale_moves(
                self.product_id, date_init, date_end, delay)
        days = (date_end - date_init).days + 1
        if days < 1:
            raise UserError(_('Date end must be greater than date init.'))
        rotation_per_day = ceil(qty_out / days)
        qty_per_day = rotation_per_day * delay
        qty_min = qty_per_day * factor_min
        qty_max = qty_per_day * factor_min * factor_max
        return qty_per_day, qty_min, qty_max, days, date_init, qty_out

    @api.model
    def schedule_compute_stock(self):
        for orderpoint in self.search([]):
            supplierinfo = orderpoint.product_id.seller_ids[0]
            company = orderpoint.company_id
            today = fields.Date.today()
            date_init = today - relativedelta(days=company.stock_period)
            date_end = today
            delay = supplierinfo.delay or company.stock_delay
            factor_min = supplierinfo.name.factor_min_stock
            factor_max = supplierinfo.name.factor_max_stock
            qty_per_day, qty_min, qty_max, days, date_init, qty_out = (
                orderpoint._compute_qtys(
                    date_init, date_end, delay, factor_min, factor_max))
            orderpoint.write({
                'product_min_qty': qty_min,
                'product_max_qty': qty_max,
            })
            msg = 'Provisioning rule updated using the following values:\n'
            msg += 'From: %s\n To: %s\n Last purchase: %s\n Sales: %s\n' % (
                date_init, date_end, date_init, qty_out)
            orderpoint.message_post(body=msg)
