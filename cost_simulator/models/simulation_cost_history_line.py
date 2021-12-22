###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class SimulationCostHistoryLine(models.Model):
    _name = 'simulation.cost.history.line'
    _description = 'Simulation Cost History Line'
    _order = 'id'

    sequence = fields.Integer(
        string='Sequence',
    )
    cost_id = fields.Many2one(
        comodel_name='simulation.cost',
        string='Cost',
        required=True,
        index=True,
        ondelete='cascade',
    )
    history_id = fields.Many2one(
        comodel_name='simulation.cost.history',
        string='Cost History',
    )
    line_id = fields.Many2one(
        comodel_name='simulation.cost.line',
        string='Cost Line',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
    )
    name = fields.Char(
        string='Name',
        required=True,
    )
    price = fields.Float(
        string='Price Unit',
        digits=(7, 2),
        default=0,
    )
    quantity = fields.Float(
        string='Quantity',
        digits=dp.get_precision('Product UoS'),
        default=1,
    )
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'),
    )
    discount_type = fields.Selection(
        selection=[
            ('included', 'Included'),
            ('visible', 'Visible'),
            ('simulation', 'Simulation')],
        string='% Type',
        default='simulation',
        required=True,
    )
    price_sale = fields.Float(
        string='Price Unit Sale',
        compute='_compute_subtotals',
    )
    quantity_sale = fields.Float(
        string='Qty Sale',
    )
    discount_sale = fields.Float(
        string='Dto. Sale',
        compute='_compute_subtotals',
    )
    subtotal_sale = fields.Float(
        string='Subtotal Sale',
        compute='_compute_subtotals',
    )
    lock_update_price = fields.Boolean(
        string='Lock update price',
    )

    @api.depends('price', 'discount', 'discount_type', 'quantity_sale')
    def _compute_subtotals(self):
        for line in self:
            price = line.price
            discount = line.discount / 100

            if line.discount_type == 'simulation':
                line.price_sale = price / (1 - discount)
                line.discount_sale = line.discount
            elif line.discount_type == 'visible':
                line.price_sale = price
                line.discount_sale = line.discount
            elif line.discount_type == 'included':
                line.price_sale = price - (price * discount)
                line.discount_sale = 0.0
            else:
                line.subtotal_sale = price
                line.discount_sale = 0.0
            subtotal = (line.price_sale * line.quantity)
            dto = line.discount_sale and (
                subtotal * (line.discount_sale / 100)) or 0
            subtotal = subtotal - dto
            if line.quantity != line.quantity_sale:
                line.price_sale = subtotal / (line.quantity_sale or 1)
            line.subtotal_sale = subtotal
            line.env['simulation.cost.history'].compute_totals()
