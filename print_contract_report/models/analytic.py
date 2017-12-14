# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
#
from openerp import models, fields


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    contract_type_id = fields.Many2one(
        comodel_name='contract.type',
        string='Contract Type'
    )
