# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.

from openerp import models, fields


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    payment_mode_id = fields.Many2one(
        comodel_name='payment.mode',
        string='Payment Mode',
        required=False)
