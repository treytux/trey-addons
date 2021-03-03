###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleOrderHistorical(models.Model):
    _name = 'sale.order.historical'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Order history'
    _order = 'date_invoiced desc, create_date desc, id desc'

    name = fields.Char(
        string='Name',
        required=True,
    )
    origin = fields.Char(
        string='Origin order',
    )
    invoice = fields.Char(
        string='Invoice',
    )
    date_invoiced = fields.Date(
        string='Date invoiced',
    )
    order_line_ids = fields.One2many(
        comodel_name='sale.order.historical.line',
        inverse_name='order_id',
        string='Order lines',
    )
    available_return = fields.Boolean(
        string='Available return',
        compute='_compute_available_return',
        store=True,
    )
    amount_total = fields.Float(
        string='Amount total',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
    )

    @api.depends('order_line_ids.available_return')
    def _compute_available_return(self):
        for order in self:
            order.available_return = any(
                [line.available_return for line in order.order_line_ids])
