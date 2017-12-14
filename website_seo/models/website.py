# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class Website(models.Model):
    _inherit = 'website'

    google_site_verification = fields.Char(
        string='Google site verification',
        help='Google site verification code provided by Search Console.')
