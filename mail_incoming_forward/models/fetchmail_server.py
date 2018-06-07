# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class FetchmailServer(models.Model):
    _inherit = 'fetchmail.server'

    forward_email = fields.Char(
        string='Forward email',
        help='Email where forwarded emails will be sent.')
