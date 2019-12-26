# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, api, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.product_id')
    @api.multi
    def _is_simulator(self):
        for order in self:
            lines = order.mapped(
                'order_line').filtered(lambda l: l.is_simulator is True)
            order.is_simulator = True if lines else False

    is_simulator = fields.Boolean(
        string='Access Simulator',
        compute=_is_simulator,
        store=True
    )
    adarra_ede_state = fields.Selection(
        string='EDE / Adarra State',
        selection=[
            ('draft', 'Draft'),
            ('simulated', 'Simulated'),
            ('send', 'Send'),
            ('purchase', 'Purchase Received'),
            ('sale', 'Sale Received'),
            ('email', 'Email Sent'),
            ('done', 'Done'),
        ],
        default='draft',
        copy=False,
        track_visibility='onchange',
    )
