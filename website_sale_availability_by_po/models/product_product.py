###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stock_state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('latest_units', 'Latest Units'),
            ('coming_soon', 'Coming Soon'),
            ('not_available', 'Not Available'),
        ],
        string='Stock State',
        compute='_compute_stock_state',
    )

    @api.depends(
        'qty_available',
        'virtual_available',
        'product_tmpl_id.available_threshold',
        'product_tmpl_id.show_availability',
    )
    def _compute_stock_state(self):
        stock_field = self.env.company.stock_field
        for product in self:
            min_qty = (
                product.product_tmpl_id.show_availability
                and product.product_tmpl_id.available_threshold or 0)
            if product[stock_field] - min_qty > 0:
                product.stock_state = 'available'
            elif product[stock_field] > 0:
                product.stock_state = 'latest_units'
            elif product.virtual_available > 0:
                product.stock_state = 'coming_soon'
            else:
                product.stock_state = 'not_available'

    def get_availability(self):
        res = {}
        for product in self:
            res[product.id] = {
                'id': product.id,
                'stock_state': product.stock_state,
                'qty_available': product.qty_available,
                'virtual_available': product.virtual_available,
                'incoming_qty': product.incoming_qty,
                'outgoing_qty': product.outgoing_qty,
                'date_planned': False}
            if product.stock_state != 'coming_soon':
                continue
            dates = product._get_availability_dates()
            future_dates = [
                date for date in dates if date >= fields.Datetime.now()]
            if future_dates:
                res[product.id].update({
                    'date_planned': min(future_dates),
                })
            elif dates:
                res[product.id].update({
                    'stock_state': 'available_shortly',
                })
        return res

    def _get_availability_dates(self):
        self.ensure_one()
        return self._get_purchase_availability_dates()

    def _get_purchase_availability_dates(self):
        self.ensure_one()
        lines = self.env['purchase.order.line'].search([
            ('order_id.state', 'in', ['purchase', 'done']),
            ('product_id', '=', self.id),
            ('order_id.date_planned_public', '=', True),
        ], order='date_planned asc')
        lines = lines.filtered(
            lambda line: line.product_qty >= line.qty_received)
        return lines.mapped('date_planned')
