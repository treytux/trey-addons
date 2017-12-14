# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api
from datetime import date, timedelta


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    initial_delivery_date = fields.Date(
        string='Initial delivery date',
        default=fields.Date.today(),
        help='Initial delivery date')

    @api.onchange('delay')
    def on_change_delay(self):
        self.initial_delivery_date = (
            date.today() + timedelta(days=int(self.delay)))

    @api.onchange('initial_delivery_date')
    def on_change_initial_delivery_date(self):
        delta = (
            fields.Date.from_string(self.initial_delivery_date) - date.today())
        self.delay = delta.days
