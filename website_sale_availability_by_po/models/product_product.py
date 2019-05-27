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
            ('not_available', 'Not Available')],
        string='Stock State',
        compute='_compute_stock_state')

    @api.one
    @api.depends('qty_available', 'incoming_qty', 'outgoing_qty')
    def _compute_stock_state(self):
        min_qty = (
            self.inventory_availability == 'threshold' and
            self.available_threshold or 0)
        if self.qty_available - min_qty - self.outgoing_qty > 0:
            self.stock_state = 'available'
        elif self.qty_available - self.outgoing_qty > 0:
            self.stock_state = 'latest_units'
        elif self.virtual_available > 0:
            self.stock_state = 'coming_soon'
        else:
            self.stock_state = 'not_available'

    @api.multi
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
            line = product.env['purchase.order.line'].search([
                ('order_id.state', '=', 'purchase'),
                ('order_id.invoice_status', '=', 'no'),
                ('product_id', '=', product.id),
                ('order_id.date_planned_public', '=', True)],
                order='date_planned asc', limit=1)
            if line:
                res[product.id].update({'date_planned': line.date_planned})
        return res
