# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, fields, models


class MailMassMailingSending(models.Model):
    _inherit = 'mail.mass_mailing.sending'

    @api.multi
    def _process_enqueued(self):
        if self.date_start <= fields.Datetime.now():
            return super(MailMassMailingSending, self)._process_enqueued()
        self.state = 'enqueued'
