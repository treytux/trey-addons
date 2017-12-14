# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class Website(models.Model):
    _inherit = 'website'

    request_accept_terms = fields.Boolean(
        string='Allow request to accept terms of privacy and use.',
        default=True)
