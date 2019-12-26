# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    days_to_notify_customer = fields.Integer(
        string='Nº of days to notify partners with exceeded credit limit',
        default=3)
