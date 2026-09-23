###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import calendar
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import _, models


class StockInventoryValuedExport(models.TransientModel):
    _inherit = 'stock.inventory.valued.export'

    def last_day(self, date):
        return calendar.monthrange(date.year, date.month)[1]

    def get_total_sales(self, product, current_month=True):
        month_start = datetime.now().replace(day=1)
        month_end = month_start.replace(day=self.last_day(month_start))
        if not current_month:
            month_start = month_start - relativedelta(months=1)
            month_end = month_start.replace(day=self.last_day(month_start))
        sale_lines = self.env['sale.order.line'].search([
            ('product_id', '=', product.id),
            ('order_id.date_order', '>=', month_start),
            ('order_id.date_order', '<=', month_end),
            ('state', 'in', ['sale', 'done']),
        ])
        return sum(sale_lines.mapped('product_uom_qty'))

    def get_orderpoint(self, product, location):
        orderpoint = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', product.id),
            ('location_id', '=', location.id),
        ], limit=1)
        return orderpoint

    def sale_average(self, months, product):
        date_start = (
            datetime.now() - relativedelta(months=months)).replace(day=1)
        date_end = datetime.now().replace(day=self.last_day(datetime.now()))
        total_sales = self.env['sale.order.line'].search([
            ('product_id', '=', product.id),
            ('order_id.date_order', '>=', date_start),
            ('order_id.date_order', '<=', date_end),
        ]).mapped('product_uom_qty')
        average = round((sum(total_sales) / months), 2)
        return average

    def get_dict(self, product, location, qty_available):
        data_dict = super().get_dict(product, location, qty_available)
        data_dict[_('Description')] = product.description or '-'
        attribute_text = ';'.join(product.attribute_value_ids.mapped('name'))
        data_dict[_('Attribute')] = attribute_text or '-'
        data_dict[_('Pending to send')] = product.outgoing_qty
        data_dict[_('Net stock')] = qty_available - product.outgoing_qty
        data_dict[_('Pending to receive')] = product.incoming_qty
        data_dict[_('Stock provided')] = (
            qty_available - product.outgoing_qty + product.incoming_qty)
        stock_moves = self.env['stock.move'].search([
            ('location_id', '=', location.id),
            ('product_id', '=', product.id),
        ], order='date desc', limit=1)
        data_dict[_('Last departure')] = (
            stock_moves and str(stock_moves.date.date()) or '-')
        stock_moves = self.env['stock.move'].search([
            ('location_dest_id', '=', location.id),
            ('product_id', '=', product.id),
        ], order='date desc', limit=1)
        data_dict[_('Last entry')] = (
            stock_moves and str(stock_moves.date.date()) or '-')
        data_dict[_('Sales current month')] = self.get_total_sales(product)
        data_dict[_('Sales last month')] = self.get_total_sales(product, False)
        data_dict[_('Average last 12 months')] = self.sale_average(12, product)
        data_dict[_('Average last 6 months')] = self.sale_average(6, product)
        data_dict[_('Average last 3 months')] = self.sale_average(3, product)
        orderpoint = self.get_orderpoint(product, location)
        data_dict[_('Minimum quantity')] = orderpoint.product_min_qty or '-'
        data_dict[_('Maximum quantity')] = orderpoint.product_max_qty or '-'
        return data_dict
