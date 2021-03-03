###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderHistoricalLine(models.Model):
    _name = 'sale.order.historical.line'
    _description = 'Order history line'

    name = fields.Char(
        string='Name',
        required=True,
    )
    quantity = fields.Integer(
        string='Quantity',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('available', 'Available'),
            ('pending', 'Pending review'),
            ('returned', 'Returned'),
            ('resolved', 'Resolved'),
            ('cancel', 'Cancelled'),
        ],
        string='State',
        default='draft',
    )
    available_return = fields.Boolean(
        string='Available return',
        compute='_compute_available_return',
    )
    available_return_date = fields.Date(
        string='Available return date',
        default=fields.Date.today(),
    )
    request_return_date = fields.Date(
        string='Request date',
    )
    return_date = fields.Date(
        string='Resolution date',
    )
    order_id = fields.Many2one(
        comodel_name='sale.order.historical',
        string='Historic order',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
    )
    price_unit = fields.Float(
        string='Price unit',
    )

    @api.depends('available_return_date')
    def _compute_available_return(self):
        for line in self:
            today = fields.Date.today()
            line.available_return = today <= line.available_return_date

    def action_resolution(self):
        self.ensure_one()
        self.return_date = fields.Date.today()
        self.state = 'draft'
