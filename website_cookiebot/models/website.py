# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp import fields, models


class Website(models.Model):
    _inherit = 'website'

    cookiebot_id = fields.Char(
        string='Cookiebot ID',
        help='This field holds the ID needed for Cookiebot functionality.',
    )
