# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class MailMessage(models.Model):
    _inherit = 'mail.message'

    message_rate = fields.Integer(
        string='Message Rating')
