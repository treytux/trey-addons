# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class PaymentMode(models.Model):
    _inherit = "payment.mode"

    payment_kutxa_type = fields.Selection(
        string='Payment type',
        default='56',
        selection=[('56', 'Transfer or direct payment'),
                   ('57', 'Check')])
    is_payment_kutxa = fields.Boolean(
        compute="_compute_is_payment_kutxa")
    expenses = fields.Selection(
        string='Movement cost payer',
        default='payer',
        selection=[('payer', 'Payer'),
                   ('beneficiary', 'Beneficiary')])
    payment_term = fields.Selection(
        string='Payment term',
        default='T',
        selection=[('C', 'Check'),
                   ('T', 'Transfer')])
    contract_number = fields.Char(
        string='Contract Number')

    @api.multi
    @api.depends('type')
    def _compute_is_payment_kutxa(self):
        payment_kutxa_type = self.env.ref(
            'payment_order_kutxa.export_kutxa')
        for record in self:
            record.is_payment_kutxa = record.type == payment_kutxa_type
