###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleSessionCashCount(models.Model):
    _name = 'sale.session.cash_count'
    _description = 'Sale session cash count'
    _rec_name = 'value'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Session',
        required=True,
        readonly=True,
    )
    type = fields.Selection(
        selection=[
            ('open', 'Open cash'),
            ('close', 'Close cash'),
        ],
        string='Type',
        required=True,
    )
    value = fields.Float(
        string='Value',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
    )
    amount_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount_subtotal',
    )

    @api.depends('value', 'quantity')
    def _compute_amount_subtotal(self):
        for line in self:
            line.amount_subtotal = line.value * line.quantity
