# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    days_to_cancel = fields.Integer(
        string='Days to cancel sale quotations',
        help='Number of days to automatically cancel the quotation sales '
             'using the scheduled action \'Cancel old quotations\'.',
        default=0)
