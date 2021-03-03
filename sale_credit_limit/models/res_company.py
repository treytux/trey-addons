# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    credit_limit_type = fields.Selection(
        selection=[
            ('blocking', 'Blocking'),
            ('warning', 'Warning'),
        ],
        string='Credit limit notification type',
        default='blocking',
    )
