# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models


class PaymentReturnLine(models.Model):
    _inherit = 'payment.return.line'

    @api.multi
    def _find_match(self):
        super(PaymentReturnLine, self)._find_match()
        before = {l.id: l.reference for l in self}
        for line in self:
            line.reference = line.concept
        super(PaymentReturnLine, self)._find_match()
        for line in self:
            line.reference = before[line.id]
