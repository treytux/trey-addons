# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields, _


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    duedate_init = fields.Date(
        string='Due Date Init')
    duedate_end = fields.Date(
        string='Due Date End')
    date_type = fields.Selection(
        selection_add=[('due_interval', _('Due Interval'))])

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)
        if self.date_type == 'due_interval':
            domain += [('date_maturity', '>=', self.duedate_init),
                       ('date_maturity', '<=', self.duedate_end)]
        return True
