# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, _


class Website(models.Model):
    _inherit = 'website'

    social_instagram = fields.Char(
        string=_('Instagram Account'),
        help=_('Instagram Account URL'))
