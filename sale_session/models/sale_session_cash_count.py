###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class SaleSessionCashCount(models.Model):
    _name = 'sale.session.cash_count'
    _description = 'Sale session cash count'
    _rec_name = 'journal_id'

    session_id = fields.Many2one(
        comodel_name='sale.session',
        string='Session',
        required=True,
        readonly=True,
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
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
    cash_count_line_ids = fields.One2many(
        comodel_name='sale.session.cash_count_line',
        inverse_name='cash_count_id',
        string='Journal cash count lines',
    )
    amount_total = fields.Float(
        string='Total',
        compute='_compute_amount_total',
    )

    @api.depends('cash_count_line_ids.value', 'cash_count_line_ids.quantity')
    def _compute_amount_total(self):
        for cash_count in self:
            cash_count.amount_total = sum([
                line.value * line.quantity for line
                in cash_count.cash_count_line_ids])
