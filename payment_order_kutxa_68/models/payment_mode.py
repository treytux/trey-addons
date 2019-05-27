# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = 'payment.mode'
    csb_suffix = fields.Char(
        string='Suffix',
        size=3,
        default='000')
    is_payment_68 = fields.Boolean(
        compute='_compute_is_payment_68')

    @api.multi
    @api.depends('type')
    def _compute_is_payment_68(self):
        payment_type_68 = self.env.ref(
            'payment_order_kutxa_68.export_payment')
        for record in self:
            record.is_payment_68 = record.type == payment_type_68
