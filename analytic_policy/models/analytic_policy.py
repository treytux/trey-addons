# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    auto_renew = fields.Boolean(
        string='Automatic renewal contract?')
    on_limit_exceeded = fields.Selection(
        selection=[
            (0, 'Stop accepting tasks'),
            (1, 'Ask before continue'),
            (2, 'Accept tasks and send invoice for extra hours'),
            (3, 'Accept tasks and invoice them at the end of the period'),
        ],
        default=1,
    )
